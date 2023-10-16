SHELL:=/bin/bash
VERSION=4.0

up:
	set -o allexport;\
	source redis/redis.env;\
	source azure.env;\
	set +o allexport;\
	docker-compose up --build

build:
ifdef nocache
	cd server && poetry lock && cd ..; \
	docker build --no-cache -t qfortier/mtgscan-server:$(VERSION) server/
else
	docker build -t qfortier/mtgscan-server:$(VERSION) server/
endif

push: build
	docker push qfortier/mtgscan-server:$(VERSION)
