# Contributing

Bug reports, reproducible examples and suggestions are welcome. Please first read [the research scope](docs/market-research.md), [security guidance](SECURITY.md) and [AGENTS.md](AGENTS.md).

Use synthetic messages for reproductions. A useful report includes the Python version, operating system, browser version, operation performed, expected result, actual result, and the smallest non-private file that reproduces the problem. Remove real addresses, names, message IDs, local paths, attachment contents and session tokens. An import receipt can itself contain private filenames or parsing details.

## Code and documentation submissions

This initial release **does not accept third-party code, assets or documentation for merge until a separate written contribution agreement is established**. Please open a descriptive issue before spending time on a patch. Opening an issue or a pull request does not silently transfer copyright or grant the publisher unrestricted relicensing rights.

The reason is concrete: the public license restricts commercial use, while the original rights holder intends to preserve a future commercial-licensing route. Outside contributions require explicit, appropriate rights for that route. Until that process exists, keep public suggestions descriptive; maintainers must not copy unlicensed snippets into the project.

Forks and modifications remain available to users for the purposes allowed by [LICENSE](LICENSE). Keep that license and [NOTICE](NOTICE) with redistributed copies. Do not change the project to MIT/Apache/GPL or call it commercially unrestricted without permission from all relevant rights holders.

## Local checks

```sh
python -m unittest discover -s tests -v
```

Exercise changed workflows in a real browser, including empty/error states, cancellation, persistence and exported-file reopening. Do not add a dependency, embedded font, icon library or copied sample without recording its source and license in [the dependency audit](docs/dependency-audit.md).
