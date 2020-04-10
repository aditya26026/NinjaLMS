## Description
(a few sentences describing the overall goals of the pull request's commits. Including a reference to the source issue, using the `#` syntax.)

### Migration and compatibility

- [ ] The merge request updates the models, as a consequences, database migrations are needed.
- [ ] The merge request breaks the compatibility.

## Related documents
(documentation and pertinent links describing the methods implemented in the merge request.)

## TODO

Before being accepted, any merge request must fulfill the following requirements:

- [ ] Check PEP8 writing style as described in [CONTRIBUTING.md](CONTRIBUTING.md).
- [ ] Ensure existing tests are still working properly.
- [ ] Features have been tested.
- [ ] Every translatable strings are written in proper english.
- [ ] Every translatable strings are tagged for translation using `gettext`, `blocktrans` and/or `trans`.
- [ ] Ensure that there is no side effect in files: changes are only related to one, and only one feature.
- [ ] Ensure that no file has been removed by accident.
- [ ] API is documented, as well as the behavior, if needed, in `docs`.
- [ ] Ensure the commit history is “clean enough” (this means no extra merge commits, etc).
- [ ] Ensure `pipeline` succeeds.

## Deploy Notes
(notes regarding deployment the contained body of work. These should note any database migration, etc.)

## Steps to Test or Reproduce
(outline the steps to test or reproduce the merge request here.)

```sh
git pull --prune
git checkout <feature_branch>
```

## Impacted Areas in Application
(list general components of the application that this merge request will affect)

/label ~"In development"
/label ~"Needs review"
