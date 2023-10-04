FROM public.ecr.aws/lambda/python:3.11

ENV PYTHONUNBUFFERED=true

COPY requirements.txt ${LAMBDA_TASK_ROOT}

RUN pip install -r requirements.txt --target ${LAMBDA_TASK_ROOT}

COPY home_monitoring ${LAMBDA_TASK_ROOT}/home_monitoring

CMD [ "home_monitoring.lambdas.metrics_importer.lambda_handler" ]
