PY = python3
VENV = ~/.virtualenvs/egg-detector
BIN=$(VENV)/bin

CAMERA_IP='192.168.1.181'
LIGHTS_PLUG_IP='192.168.1.150'
LIGHTS_PLUG_PORT=0
DEV_ACCOUNT=599598955234
IMAGE_NAME="egg_detector"
ON_PREM_HOST="media-server"

.PHONY: build-mac
build-mac: 
	@docker build -t ${IMAGE_NAME}_arm -f ./Dockerfile . --platform=linux/arm64

.PHONY: run-mac
run-mac: build-mac
	docker run -e CAMERA_IP='${CAMERA_IP}' \
	           -e LIGHTS_PLUG_IP='${LIGHTS_PLUG_IP}' \
	           -e LIGHTS_PLUG_PORT=${LIGHTS_PLUG_PORT} \
	           -e ENVIRONMENT='dev' \
	           -v `pwd`/output:/app/output \
	           -v ${HOME}/.aws/credentials:/root/.aws/credentials:ro \
	            ${IMAGE_NAME}_arm

.PHONY: build
build: 
	@docker build -t ${IMAGE_NAME} -f ./Dockerfile . --platform=linux/amd64

.PHONY: deploy
deploy: test
	docker save -o /tmp/${IMAGE_NAME}.tar ${IMAGE_NAME}:latest
	scp /tmp/${IMAGE_NAME}.tar nick@media-server:~/images
	ssh ${ON_PREM_HOST} 'docker load -i ~/images/egg_detector.tar && mkdir -p ~/egg-detector'
	scp Makefile ${ON_PREM_HOST}:~/egg-detector
	rm /tmp/${IMAGE_NAME}.tar

# runs the egg detector app on the on-prem server (assumes deploy has been run from development machine)
run:
	docker run -e CAMERA_IP='${CAMERA_IP}' \
	           -e LIGHTS_PLUG_IP='${LIGHTS_PLUG_IP}' \
	           -e LIGHTS_PLUG_PORT=${LIGHTS_PLUG_PORT} \
	           -v `pwd`/output:/app/output \
	           -v ${HOME}/.aws/credentials:/root/.aws/credentials:ro \
	            ${IMAGE_NAME}

.PHONY: test
test: build-mac
	docker run ${IMAGE_NAME}_arm sh -c "cd /app && pytest --ignore reolinkapipy"
