# Eitan's Solution
Redis is an open-source, in-memory data structure store used primarily as a high-performance database, cache, and message broker. By keeping data in RAM rather than on a disk, it delivers sub-millisecond response times for massive volumes of real-time applications.

## Step 1 - Running redis on docker and connecting with python
I pulled the docker image, created a network configuration and ran the image using these commands:

``` 
docker pull redis:7-bookworm
docker network create –subnet=172.16.0.0/20 redis-network
docker run --name redis-server --net redis-network --ip 172.16.0.2 -p 6379:6379 -d redis:7-bookworm
```
Now there's a docker container running with a redis server running on it. I ran redis-cli on the container:
```
docker exec -it redis-server redis-cli
```
And I got a prompt (running localy on the container) in which I can send get/set commands to the redis server.
The server is listening on port 6379 (tcp), so I wrote a simple python script that connects to redis server using the redis python package.
I ran the script on my ubuntu which is the docker host, and I made sure that it connects and works.

## Step 2 - Writing a test suite
I wrote a test suite using pytest, that validates the redis server functionality (See [test_redis.py](test_redis.py)).
I ran the tests on the original redis:7-bookworm image and all the tests passed.
Later when I edit the image and fix vulnerabilities, I'll run the tests on it to make sure it functions as expected.

## Step 3 - Building the image manually
There's an [official repo](https://github.com/redis/docker-library-redis/tree/master) with a dockerfile for each redis version.
I used the docker file of version 7.4 for Debian (I checked the version of the redis_server in the redis:7-bookworm image and it's 7.4.7). 
I copied the ```Dockerfile``` and the ```docker-entrypoint.sh```, and I ran:

```
docker build -t custom-redis .
```

The docker was built sucessfuly, I ran it. Then I ran the tests and they passed.

## Step 4 - Running grype
I ran grype on the original image and on the image I built by myself, and I compared the outputs:

```
grype redis:7-bookworm > original
grype custom-redis > custom
sort original > original.sorted
sort custom > custom.sorted
diff original.sorted custom.sorted
```

Diff's output was clean - meaning the image I built is identical to the original redis image and has the same vulnerabilities.

## Step 5 - Examining the vulnerabilities
There are 3 types of CVE's listed in the scan result:
- binary - vulnerabilities in redis server's code itself, written directly by redis developers.
- deb - vulnerabilities in debian, for example in user-space binaries, in C's standard library, or in other libraries.
- go-module - vulnerabilities in GO.

There are 2 vulnerabilities of redis, non of them got fixed in later versions. I can fix them by editing their code directly (There's no other way to do it). 
There are many go-module vulnerabilities that got fixed in later GO versions. I can fix them by upgrading GO's version.



























