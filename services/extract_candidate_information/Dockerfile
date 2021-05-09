# GLOBAL VARIABLES
ARG FUNCTION_DIR="/extract_candidate_information"

FROM python:buster as build-image

# INSTALLING LAMBDA RUNTIME INTERFACE CLIENT
ARG FUNCTION_DIR
RUN apt-get update && apt-get install -y g++ make cmake unzip libcurl4-openssl-dev
RUN mkdir -p ${FUNCTION_DIR}
RUN pip install --target ${FUNCTION_DIR} awslambdaric


FROM python:buster

# INSTALLING SYSTEM DEPENDENCIES FOR THE FUNCTION
ARG FUNCTION_DIR
WORKDIR ${FUNCTION_DIR}
COPY requirements.txt ${FUNCTION_DIR}
RUN apt-get update && apt-get install -y antiword python-dev libxml2-dev libxslt1-dev antiword unrtf poppler-utils \
tesseract-ocr flac ffmpeg lame libmad0 libsox-fmt-mp3 sox libjpeg-dev swig zlib1g-dev
# pstotext

# INSTALLING PYTHON DEPENDENCIES FOR THE FUNCTION
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN python -m spacy download en_core_web_md
RUN python -m spacy download es_core_news_md

# SETTING ALL THE FILES NEEDED
COPY --from=build-image ${FUNCTION_DIR} ${FUNCTION_DIR}
COPY function ${FUNCTION_DIR}/function
COPY entry_script.sh /entry_script.sh
ADD https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/latest/download/aws-lambda-rie /usr/local/bin/aws-lambda-rie
RUN chmod +rx /usr/local/bin/aws-lambda-rie

# SET THE ENTRY POINT
ENTRYPOINT [ "/entry_script.sh" ]
CMD ["function.app.handler"]
