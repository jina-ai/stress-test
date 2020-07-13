#!/bin/sh
TEST_WORKDIR=./faiss_data/
mkdir -p ${TEST_WORKDIR}
cd ${TEST_WORKDIR}
curl ftp://ftp.irisa.fr/local/texmex/corpus/sift.tar.gz --output sift.tar.gz
tar zxf sift.tar.gz
