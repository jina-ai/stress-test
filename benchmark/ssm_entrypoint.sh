#!/bin/bash

HOME_DIR=/mnt/data

for arg in "$@"; do
    shift
    case "$arg" in
        "--help")               set -- "$@" "-h" ;;
        "--jina-compilation")   set -- "$@" "-j" ;;
        "--jina-branch")        set -- "$@" "-b" ;;
        *)                      set -- "$@" "$arg"
  esac
done

while getopts "hj:b:" opt
do
  case "$opt" in
    "h") print_usage; exit 0 ;;
    "j") COMPILATION=${OPTARG} ;;
    "b") BRANCH=${OPTARG} ;;
    "?") print_usage >&2; exit 1 ;;
  esac
done

echo $COMPILATION
echo $BRANCH

if [[ -n "$COMPILATION" ]]; then
    echo "Jina will be downloaded via ${COMPILATION}"
else
    COMPLIATION=pip
    echo "Selecting Jina download to be ${COMPLIATION} as no params are passed\n"
    pip3 install jina
fi

if [[ $COMPILATION == "git" ]]; then
    if [[ -n "$BRANCH" ]]; then
        echo "Jina will be downloaded via ${BRANCH} branch"
    else
        BRANCH=master
        echo "Selecting Jina download to be from ${BRANCH} branch"
    fi
    git clone -b $BRANCH --single-branch https://github.com/jina-ai/jina.git $HOME_DIR
    cd $HOME_DIR/jina && pip3 install '.[match-py-ver]' --no-cache-dir
fi

cd $HOME_DIR/stress-test/benchmark
pip3 install -r requirements.txt
python3.8 app.py --input-type $INPUT_TYPE --index-yaml $INDEX_YAML --query-yaml $QUERY_YAML \
    --num-bytes-per-doc $NUM_BYTES_PER_DOC --num-chunks-per-doc $NUM_CHUNKS_PER_DOC \
    --num-sentences-per-doc $NUM_SENTENCES_PER_DOC


# cd && git clone -b $ST_BRANCH --single-branch https://github.com/jina-ai/stress-test.git
# cd stress-test/benchmark && pip3 install -r requirements.txt


