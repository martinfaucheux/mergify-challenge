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

# Stack

- uv as python manager
- fast api as web framework
- httpx as http client
