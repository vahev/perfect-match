FROM public.ecr.aws/lambda/python:3.8

ARG FUNCTION_DIR="consume_workable"
RUN mkdir -p ${FUNCTION_DIR}
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY function ${FUNCTION_DIR}

CMD ["consume_workable.app.handler"]
