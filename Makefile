DOT_ENV=.env
GITHUB_NETRC=${HOME}/.netrc
GITHUB_NETRC_CI=${GITHUB_WORKSPACE}/netrc
DOCKER_REGISTRY=888888888888.dkr.ecr.ap-northeast-1.amazonaws.com

CNAME=pytemplate
PACKAGE_NAME=pytemplate

TEST_SRC=/root/tests/data/
TEST_DST=/root/tests/data/

build:
	DOCKER_BUILDKIT=1 docker build \
	--progress=plain \
	--build-arg PACKAGE_NAME=${PACKAGE_NAME} \
	--build-arg POETRY_WITHOUT="--without dev" \
	--secret id=github,src="${GITHUB_NETRC}" \
	-t ${DOCKER_REGISTRY}/${CNAME}:latest \
	-f Dockerfile .

test:
	docker run -it --rm \
	-v ${PWD}/${PACKAGE_NAME}/:/root/${PACKAGE_NAME} \
	-v ${PWD}/tests:/root/tests \
	${DOCKER_REGISTRY}/${CNAME}:latest python run.py --src ${TEST_SRC} --dst ${TEST_DST}

build-ci:
	DOCKER_BUILDKIT=1 docker build \
	--progress=plain \
	--build-arg PACKAGE_NAME=${PACKAGE_NAME} \
	--build-arg POETRY_WITHOUT="--without dev" \
	--secret id=github,src="${GITHUB_NETRC_CI}" \
	-t ${DOCKER_REGISTRY}/${CNAME}:latest \
	-f Dockerfile .

# No TTY mode
test-ci:
	docker run -i --rm \
	-v ${PWD}/${PACKAGE_NAME}/:/root/${PACKAGE_NAME} \
	-v ${PWD}/tests:/root/tests \
	${DOCKER_REGISTRY}/${CNAME}:latest python run.py --src ${TEST_SRC} --dst ${TEST_DST}

precommit-install:
	poetry run pre-commit install

precommit-update:
	poetry run pre-commit autoupdate

check:
	poetry run pre-commit run --all-files

pytest:
	poetry run pytest -s

pytest-dist:
	poetry run pytest -s -n auto

pytest-dist-all:
	poetry run pytest -s -n auto --runslow

coverage-pytest:
	poetry run pytest --cov-report lcov --cov=${PACKAGE_NAME} -s --runslow

coverage-pytest-dist:
	poetry run pytest --cov-report lcov --cov=${PACKAGE_NAME} -s -n auto --runslow

coverage-report:
	poetry run coverage report -m
	poetry run coverage lcov -o lcov.info

coverage:
	@make coverage-pytest
	@make coverage-report

coverage-dist:
	@make coverage-pytest-dist
	@make coverage-report

sphinx-apidoc:
	poetry run sphinx-apidoc -F -o docs/source ${PACKAGE_NAME}/

sphinx:
	poetry run sphinx-build docs/source docs/build
