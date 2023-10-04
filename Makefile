.DEFAULT_GOAL := all
PY = python3
VENV = ~/.virtualenvs/home-monitoring
BIN=$(VENV)/bin

PROD_ACCOUNT = 312658751905
DEV_ACCOUNT = 599598955234
IMAGE_NAME = "home_monitoring"

.PHONY: build
build: test
	@docker build -t ${IMAGE_NAME} -f ./Dockerfile . --platform=linux/amd64

.PHONY: upload-image
upload-image: build
	@aws --profile default ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin ${DEV_ACCOUNT}.dkr.ecr.us-west-2.amazonaws.com
	@docker tag ${IMAGE_NAME}:latest ${DEV_ACCOUNT}.dkr.ecr.us-west-2.amazonaws.com/${IMAGE_NAME}:latest
	@docker push ${DEV_ACCOUNT}.dkr.ecr.us-west-2.amazonaws.com/${IMAGE_NAME}:latest

.PHONY: deploy-dev
deploy-dev: upload-image 
	@for function_name in `aws --profile default lambda list-functions | jq -r '.Functions[] | .FunctionName'`; do \
            aws --profile default --no-cli-pager lambda update-function-code --function-name $${function_name} --image-uri ${DEV_ACCOUNT}.dkr.ecr.us-west-2.amazonaws.com/${IMAGE_NAME}:latest ; \
	done

.PHONY: deploy-prod
deploy-prod:  upload-image
	@for function_name in `aws --profile home-monitoring-prod lambda list-functions | jq -r '.Functions[] | .FunctionName'`; do \
            aws --profile home-monitoring-prod --no-cli-pager lambda update-function-code --function-name $${function_name} --image-uri ${DEV_ACCOUNT}.dkr.ecr.us-west-2.amazonaws.com/${IMAGE_NAME}:latest  ; \
	done

.PHONY: docker-run
docker-run: build
	@docker run -v ${HOME}/.aws/credentials:/root/.aws/credentials:ro \
		     -p 9000:8080 \
		     -e ENVIRONMENT='dev' \
		     ${IMAGE_NAME}:latest

$(VENV): requirements.txt requirements-dev.txt setup.py
	$(PY) -m venv $(VENV)
	$(BIN)/pip install --upgrade -r requirements.txt
	$(BIN)/pip install --upgrade -r requirements-dev.txt
	$(BIN)/pip install -e .
	touch $(VENV)

# runs the PingScraper. This is meant to be invoked from an on-prem machine
run-ping: $(VENV)
	cd ~/home-monitoring
	. $(BIN)/activate && ENVIRONMENT=prod python ping.py

.PHONY: lint
lint: $(VENV)
	@$(BIN)/flake8
	@tflint --recursive --config "`pwd`/.tflint.hcl"

.PHONY: format
format: $(VENV)
	$(BIN)/black .

.PHONY: test
test: $(VENV)
	$(BIN)/pytest --ignore=egg-detector

clean:
	rm -rf $(VENV)
	find . -type f -name *.pyc -delete
	find . -type d -name __pycache__ -delete

.PHONY: tf-init
tf-init:
	terraform -chdir=terraform/environments/dev init
	terraform -chdir=terraform/environments/prod init

.PHONY: tf-apply-dev
tf-apply-dev:
	terraform -chdir=terraform/environments/dev apply -var-file=config.tfvars

.PHONY: tf-apply-prod
tf-apply-prod:
	terraform -chdir=terraform/environments/prod apply -var-file=config.tfvars

