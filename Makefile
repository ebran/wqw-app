.phony:	build run

all:	build run

build:
		docker build \
			-f Dockerfile \
			-t wqw-app .

analyze:
		dive build \
			-f Dockerfile \
			-t wqw-app .

run:
		docker run \
			--name wqw-app \
			--rm \
			-it \
			wqw-app bash
			