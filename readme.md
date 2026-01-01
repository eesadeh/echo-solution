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
The debian vulnerabilities require creating a new image of debian, and it's the most expensive solution, so I won't do it.

## Step 6 - Fixing redis CVE
CVE 2025-49112 is about an integer underflow, and a possible solution is listed [here](https://github.com/valkey-io/valkey/pull/2101). So all I got to do is to change the condition in line 783 in src/networking.c to:
```
prev->size > prev->used
```
The Dockerfile fetches the source code directly on the container:
```
wget -O redis.tar.gz "$REDIS_DOWNLOAD_URL";
mkdir -p /usr/src/redis;
tar -xzf redis.tar.gz -C /usr/src/redis --strip-components=1;
```
So I added the file modification right after:
```
sed -i 's/prev->size - prev->used > 0/prev->size > prev->used/g' /usr/src/redis/src/networking.c;
```
This command replaces the condition in networking.c. 
After building the image and scanning it with grype, I compared the result and the original scan, and there was no difference. CVE 2025-49112 was listed also after fixing the issue. I read in the internet that grype lists CVEs according to the software's version, meaning that a change in the source code doesn't effect grype's scan result, but the CVE was fixed.
I ran the tests and they all passed.

## Step 7 - Fixing GO CVEs
All GO CVEs can be resolved by upgrading go module version. 
Upgrading GO to 1.20.7 should resolve at least 10 CVEs.
After examining the Dockerfile, I found that the binary gosu is the cause for the image to have GO libraries.
The DockerFile sets gosu version through an environment variable:
```
ENV GOSU_VERSION 1.17
```
It uses version 1.17 while the most updates version is 1.19. I checked in gosu's repo and version 1.19 uses GO 1.24.6 - Enough for resolving at least 10 CVE's.
So I changed the value in the Dockerfile to be:
```
ENV GOSU_VERSION 1.19
```
In addition, the number 1.17 is hardcoded in several urls right below, that links to gosu sources. I changed the number in all the links to 1.19. There's also a sha-256 linked to each url, and there's a validation using sha256sum:
```
echo "$sha256 */usr/local/bin/gosu" | sha256sum -c -;
```
The binaries are different in the newer version, so I deleted the validation in the Dockerfile, but a better approach would be to change the sha-256s to the updated ones (To prevent MITM attacks).

After running grype on the new image, I got only 12 go-module CVEs compared to 65 go-module CVEs in the original scan.

## Summary
I had some experience with docker so it wasn't too challenging. I used WSL2 as my ubuntu so I had some problems with that - mostly with setting an IP to my container, windows-linux text files format differences (like \r\n), and memory limitations (That's why I had to change the `make` command in the Dockerfile to work slower only with 1 thread).
As for lessons, this exercise made it clear that every product we use should be updated, but also then there will be vulnerabilities. It doesn't matter how safe you write you code, you'll always have so many vulnerabilities coming from the OS or libraries you use.

Most vulnerabilities left are vulnerabilities in debian. Most of these CVE's didn't get fixed in any debian version. Therefore, the only way to fix them is editing debian source code and compiling it by myself. There are also 12 more go-module CVEs, which were'nt addressed om the last gosu version. All of them got fixed in later GO versions, so a solution here would be editing gosu source code to use the latest GO version. There's also 1 redis CVE that I didn't resolve. Editing redis source code is once again the solution here. As of priority - redis CVE's are the most priorotized to fix because redis manages the communication with the outer world - and attackers can get access to the machine through vulnerabilities in it. Next prioratized are some of the debian vulnerabilities, which redis directly use - for example libc CVEs or maybe encryption CVEs, because these can be used as well to get access to the machine. Then the rest of the debian vulnerabilities and the go-module vulnerabilities should be fixed, as they can be used to grant root-access once you have an access to the machine as a less powered user.

The original image size is 175MB while new image size is 172MB.
