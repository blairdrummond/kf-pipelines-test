#!/usr/bin/env sh

while test -n "$1"; do
    case "$1" in
        --output)
            shift
            OUTPUT="$1"
            ;;

        --params)
            shift
            JSON="$1"
            ;;

        *)
            echo "Invalid option $1; allowed: --params --options" >&2
            exit 1
            ;;
    esac
    shift
done

echo "JSON: -> _${JSON}_"
echo "MINIO: -> _${S3_ENDPOINT}_"

test -z "$JSON" && exit 0

mkdir -p /output

echo "$JSON" | jq '.' | tee /output/out.json

mc config host add daaas \
    "http://$S3_ENDPOINT" "$AWS_ACCESS_KEY_ID" "$AWS_SECRET_ACCESS_KEY"

mc cp -r /output "daaas/$OUTPUT"

echo "Done."
