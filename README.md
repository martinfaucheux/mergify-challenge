# Stargazer fetcher

API that fetches "neighbour" repositories of GitHub repositories based on shared stargazers.

More detail for the challenge [here](https://mergify.notion.site/Stargazer-4cf5427e34a542f0aee4e829bb6d9035)

Stack

- uv as python manager
- fast api as web framework
- postgresql as database with ModelSQL as ORM
- docker for containerization
- github actions for CI/CD
- render for deployment

Disclaimer: As it was not explicitely mentioned in the challenge description, I took the liberty of using GitHub copilot to assist me in writing some parts of the code.

# API Endpoints

## Documentation

The documentation is available

- locally after running the app at `localhost:8000/docs` once the app is running.
- on the deployed environment at `https://mergify-challenge.onrender.com/docs`

To authenticate, pass a valid API key in the `X-API-KEY` header.

## TLDR

To fetch neighbour repositories for a given repository with the provided test key, you can use the following curl command:

```bash
curl -X 'GET' \
  'https://mergify-challenge.onrender.com/repos/alamorre/django_ec2_complete/starneighbours' \
  -H 'accept: application/json' \
  -H 'X-API-Key: 8grZWT6jzcUAoUeh6amnpNv4FhpLc0BFbqojxReJHWd'
```

the example uses this repo for test: [alamorre/django_ec2_complete](https://github.com/alamorre/django_ec2_complete)

# Run it locally

## Setup

Clone this repository:

```bash
git clone git@github.com:martinfaucheux/mergify-challenge.git
cd mergify-challenge
```

generate a `.env` file from the `.env.example` file:

```bash
cp .env.example .env
```

Generate a GitHub token [here](https://github.com/settings/personal-access-tokens). It doesn't need any special permissions.
Then paste it in the `.env` file.

This project uses docker compose. To run it, simply execute:

```bash
docker compose up --build
```

The API docs are available at: `http://localhost:8000/docs`

To genereate an API key for testing, you can use the following python snippet:

```bash
docker compose exec api uv run python cli.py create_api_key username user@mail.com
```

## Testing

To run the tests, execute the following command:

```bash
docker compose exec api uv run pytest
```

# Deployed environment

This app is deployed on render at https://mergify-challenge.onrender.com/

It might take a few seconds to spin up the instance if it's not used recently as it runs under the free plan.

you can use the following key for testing: `8grZWT6jzcUAoUeh6amnpNv4FhpLc0BFbqojxReJHWd`

# Notes and improvement

## Choice a framework

I am more familiar with django but for this project I wanted to try fastapi as it is more lightweight and performant for building APIs thanks to its async capabilities, espcially for this project where we have to deal with a lot of long I/O operations.

Retrospectively, it would have taken me way less time to spin up a POC with django as I am more used to it and it has more built-in features that would have simplified the implementation (like authentication, admin interface, etc).

## Github fetching

My first attempt was to use the GitHub REST API as I am more familiar with this type of API. After some digging it turned out that the GraphQL API is usually a better fit for this type of request as it allows to fetch stargazers and repositories in a more efficient way, reducing the number of requests needed.

I experimented with the graphql queries on a separate branch [`graphql`](https://github.com/martinfaucheux/mergify-challenge/tree/graphql) but as GH graphql rate limit is based on the underlying query complexity (ie the number of relations), it was difficult to size the max stargazer count versus max repo count without hitting the maximum allowed points. I didn't get any result for larger repositories either.

My first improvement would be to dig more into the graphql approach by adding more retry mechanism in case of too many points used.

## Performances

In the current state, my API is very slow if not unusable for repositories with a lot of stargazers (100+). The main bottleneck is the fetching of stargazers from GitHub as it requires multiple requests.

An easy improvement would be to use a background job system with celery: when making a request, instead of returning the result directly, we could enqueue a job to fetch the stargazers and return a job id. The client could then poll the job status endpoint to get the result when it's ready. It would allow to tackle larger repositories without hitting request timeouts.

Chaching some GitHub request might also help improve performance for frequently requested repositories, especially bigger ones. A reddis instance could be used for that.

## Auth scheme

For an API as simple as this one, an API key authentication scheme is sufficient. In a more complex scenario, I would consider using OAuth2 or JWT tokens for better security and scalability.

I thought about having only a single valid API key stored in environment variables for simplicity and not to have to plug a db, but I ended up saving it in the database to allow easier extension in the future (multiple keys, key revocation, usage tracking, etc).
