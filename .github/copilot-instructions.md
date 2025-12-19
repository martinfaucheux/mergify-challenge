This is an API that fetches "neighbour" repositories of GitHub repositories based on shared stargazers.

# Context

GitHub provides a feature allowing a user to [save a repository with a star](https://docs.github.com/en/get-started/exploring-projects-on-github/saving-repositories-with-stars). Those users are called _stargazers._ This feature is great for users to bookmark repositories. It is also quite interesting for maintainers as they can know the number of people that are interested in their project. It is said that the more stars a repository gets, the more popular the project is! 🚀

# The App

We would like to leverage those stars to find neighbours of a repository. **We define a neighbour of a repository A as a repository B that has been starred by a same user.**

> For example, if joe adds a star to the repository projectA and projectB, we define those repositories projectA and projectB as being _neighbours_.

Of course, the more users two projects have in common the closer they are. ## API endpoint The goal of this project is to have a web service that can receive such a request:

```
GET /repos/<user>/<repo>/starneighbours
```

This endpoint must return the list of neighbours repositories, meaning repositories where at least one stargazer is found in common. The returned JSON format should look like:

```json
[
  { "repo": <repoA>, "stargazers": [<stargazers in common>, ...], },
  { "repo": <repo>, "stargazers": [<stargazers in common>, ...], }, ...
]
```

# 2. API Authentication 🔑

Now that your API endpoint is ready, we'd like to add support for authentication on top of it.

API keys can be generated from a command. This will create a new user in the database and generate an API key for them.

The key should be checked at each request to the `/repos/<user>/<repo>/starneighbours` endpoint. If the key is missing or invalid, a `401 Unauthorized` response should be returned.

# Stack

- uv as python manager
- fast api as web framework
- httpx as http client

# Extra details

User model

- id: uuid
- username: str
- email: str
- api_key: str
- api_key_valid_until: datetime
- created_at: datetime
