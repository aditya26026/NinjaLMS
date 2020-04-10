## Description

This is the **Merge Request** for the `PACKAGE_NAME` vX.X.X release.

(a few sentences describing the overall goals of the pull request's commits, the purpose of this release, if it’s a beta, stable, etc.)

### Migration and compatibility

- [ ] The merge request updates the models, as a consequences, database migrations are needed.
- [ ] The merge request breaks the compatibility.

## General TODO

Before being accepted, any merge request must fulfill the following requirements:

- [ ] Check PEP8 writing style as described in [CONTRIBUTING.md](CONTRIBUTING.md).
- [ ] Ensure existing tests are still working properly.
- [ ] Features have been tested.
- [ ] Every translatable strings are written in proper english.
- [ ] Every translatable strings are tagged for translation using `gettext`, `blocktrans` and/or `trans`.
- [ ] Ensure that there is no side effect in files: changes are only related to one, and only one feature.
- [ ] Ensure that no file has been removed by accident.
- [ ] API is documented, as well as the behavior, if needed, in `docs`.
- [ ] Ensure `pipeline` succeeds.

## Release TODO

- [ ] Globally update API documentation.
- [ ] Globally update external documentation located in `docs`.
- [ ] Update and add (where missing), licence headers and contributions.
- [ ] Update the `__init__.py` version with the appropriate version number: `vX.X.X`.
- [ ] Update the [CHANGELOG](CHANGELOG.md) file.

## Current changelog

(the list of changes that will be included in the [CHANGELOG](CHANGELOG.md) file)
