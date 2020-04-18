#!/bin/python3

import json
import re
nicename = re.compile('^[0-9a-zA-Z_-]+$')
bucketname = re.compile('^[0-9a-z_-]+$')


EXPERIMENT_NAME = "wIFR-Sensitivity-Analysis"
OUTPUT_BUCKET = 'wifr-analysis'
PIPELINE_NAME = "Ken-Pipeline"
IMAGE_NAME = "blair-kf-pipeline-test:v5"

assert bucketname.match(OUTPUT_BUCKET)
assert nicename.match(EXPERIMENT_NAME)
assert nicename.match(PIPELINE_NAME)


# Ken's experiment
# This gets used in the sensitivity simulation.
def wifr_space(how_many=5, MIN_wIFR=0.8*0.007924, MAX_wIFR=1.2*0.011526):
    """
    Specify how you create the wIFR parameters.
    This example takes N random (uniform) samples
    from an interval.

    Returns generator of: { "ON" : 0.023, "BC" : 0.0094, ... }
    """

    from numpy.random import uniform

    CANADA = [
        "BC", "AB", "SK", "MB", "ON", "QC", "NB", "NL", "NS", "PE",
        "YK", "NT", "NV"
    ]

    for _ in range(how_many):
        wIFRs = uniform(MIN_wIFR, MAX_wIFR, len(CANADA))
        weights = dict(zip(CANADA, wIFRs))
        yield weights



###################################
### DON'T EDIT:                 ###
### Create the Experiment       ###
###################################
import kfp
client = kfp.Client()
exp = client.create_experiment(name=EXPERIMENT_NAME)


###################################
### DON'T EDIT:                 ###
### Register our storage output ###
###################################
import defaults
defaults.make_bucket(OUTPUT_BUCKET)

###################################
### You can change below this   ###
### Create the pipeline         ###
###################################
from kfp import dsl

def the_pipeline(params, output):
    return dsl.ContainerOp(
        name=PIPELINE_NAME,
        image=f'k8scc01covidacr.azurecr.io/{IMAGE_NAME}',
        arguments=[
            '--params', params,
            '--output', output,
        ]
    )


@dsl.pipeline(
    name="Fatality of Infected Ratio Analysis",
    description='Test sesitivity to the wIFR'
)
def sensitivity_simulation(output):
    for (i, param) in enumerate(wifr_space()):
        the_pipeline(json.dumps(param),  f'{output}/data/{i}')

    # Do you need this?
    defaults.inject_env_vars()


from kfp import compiler
compiler.Compiler().compile(
    sensitivity_simulation,
    EXPERIMENT_NAME + '.zip'
)


###################################
### DON'T EDIT:                 ###
### Ship the pipeline to run    ###
###################################

import datetime
import time



run = client.run_pipeline(
    exp.id,
    EXPERIMENT_NAME + '-' + time.strftime("%Y%m%d-%H%M%S"),
    EXPERIMENT_NAME + '.zip',
    params={
        'output': OUTPUT_BUCKET
    }
)
