# Introduction

## Hey there, feel welcome!

We’re very happy to see you here, with the wish to **contribute to ~~our~~ your project**, **Koala LMS**. Please, read the following sections in order to know how to **ask questions**, **report bugs** or **contribute** to the code of **Koala LMS** and its applications.

Those guidelines are meant to give you answers about the contribution process. Having something formalized helps us to manage contributions and gives you a guide to do so.

**Koala LMS** would like to be an **open community** where everyone has something to give. We are looking for translators, documentation writers, communication specialists, developers and **everyone that wishes to contribute** using its own abilities.

Please, don't use the issue tracker for support questions. We plan to add things like mailing lists or IRC channels in case some help is required.

## :exclamation: Responsibilities

* Assume people mean well: when you’re discussing or debating with others, please assume they mean well. We’re here to cooperate 🙃.
* Ensure your changes run on Firefox, Google Chrome (and Edge, even if few people care!).
* Ensure your code respects the [Python PEP8 standards](https://www.python.org/dev/peps/pep-0008/) (we’ve got a pipeline to check that).
* Ensure your strings are written in a proper English.
* Ensure the strings you changed are also present in the [`gettext`](https://www.gnu.org/software/gettext/manual/gettext.html#Why) PO files. Please, refer to the [Django documentation on internationalisation](https://docs.djangoproject.com/en/2.2/topics/i18n/). `gettext` is the utility used in almost every software development project in order to localise strings showed to the end users.
* If you wish to make major changes or enhancements, **open an issue** to discuss about it. Discuss things transparently and get community feedback.
* Be welcoming to newcomers and encourage diverse new contributors from all backgrounds. See the [Python Community Code of Conduct](https://www.python.org/psf/codeofconduct/).

## :construction_worker: Your First Contribution

### Prerequisites

As part of your first contribution, there are a few things and skill you have to acquire or to already have:
* [x] You are comfortable with HTML, Javascript and CSS languages and technologies.
* [x] You are able to understand and to write [Python](https://www.python.org/) code.
* [x] You know what is Bootstrap and how to use [Bootstrap 4](https://getbootstrap.com/docs/4.0/getting-started/introduction/).
* [x] You know what is a [web framework](https://en.wikipedia.org/wiki/Web_framework) and you understand its behaviour, without depending on which one it is, [Symfony](https://symfony.com/), [Flask](https://flask.palletsprojects.com/en/1.1.x/), etc.
* [x] **Koala LMS** is written in **Python** using the web framework **Django** and uses **Bootstrap** as its CSS Framework. The last thing you have to do before contributing is to complete the [Django tutorial](https://docs.djangoproject.com/en/2.2/intro/tutorial01/) is order to understand how **Django** works, and to better understand the **Koala LMS** code.

### Finding Something To Do

If you’re not sure on where to start, we tagged some issues with the ~newcommer flag. You can pick this issue and start working on it. We supposed those issues could be fixed with only a few lines, and tests. The ~"help wanted" tagged issues are a bit more complicated, it’s the next step for you 😉.

If you don’t know which one you should take, watch the votes or issues to see the impact the change may have for the developers and users.

# :snake: Installing the Development Environment

Koala LMS is a **Django project** that includes **two Django apps**. If this is not clear to you, please refer to the seventh step of the tutorial, [Advanced tutorial: How to write reusable apps](https://docs.djangoproject.com/en/2.2/intro/reusable-apps/). It is organized as shown below: `koala-lms` depends on two apps, `accounts` (in order to manage users and accounts) and `learning` (in order to manage courses, activities and resources). `learning` needs `accounts` to work properly but `accounts` remains an **independent Django application** you can use in any other Django project.

![Koala LMS package organisation](./docs/img/package-organisation.png)

By doing this, we allow people to **develop other applications** that can be **plugged** into Koala LMS in order to extend it. We want to allow things to be minimised, or extended, depending on users’ particular use cases.

For this section, we will refer to your **project directory**, this is a directory that is, for instance, called `koala_lms` in your home folder. Let’s create it:
```bash
mkdir ~/koala_lms
```

## Install Koala LMS

First things first, you have to `clone` the Koala LMS application in your project folder.
```bash
git clone git@gitlab.com:koala-lms/lms.git lms
```

Remote `origin` now points to the official repository. If you forked the project, clone your project from your **OWN NAMESPACE**. Then, you can install the dependencies using `pip`. Switch to the proper `branch` and run `pip3 install -r requirements.txt`. You might configure a [Python virtual environment](https://docs.python.org/3/library/venv.html) for this project. See [Prepare Your workspace](#prepare-your-workspace) in order to install a virtual environment.

**Note**: there are two branches in Koala LMS development: `master` for stable things, from which tags and versions are released, and `develop` that contains the current development work, which keep the [online demo at demo.koala-lms.org](https://demo.koala-lms.org) updated.

### Prepare your workspace

Before working on Koala LMS, you need to prepare your workspace: it will contain your [Python virtual environment](https://docs.python.org/3/library/venv.html), as long as the Django Project, **lms** and the applications you are working on: **django-learning**, **django-accounts**, etc. Before doing so, ensure you use Python 3.7 or greater, and that you can use the `virtualenv` Python module. If not, documentation [for Ubuntu](https://linuxize.com/post/how-to-create-python-virtual-environments-on-ubuntu-18-04/), or [for Fedora](https://developer.fedoraproject.org/start/sw/web-app/django.html).

1. Move into your **project directory**, here `koala_lms`
2. Create a Python virtual environment with: `python3 -m venv py3venv`. This creates a directory, `py3venv` which contains the files related to your environment, and the dependencies.
3. Activate your Python virtual environment, using `source py3venv/bin/activate`. The prompt now changes and you see `py3venv` at the very beginning of the command line.

### Download and use the latest version of Koala LMS

1. In your **project directory**, clone the **Koala LMS** Git repository using `git clone https://gitlab.com/koala-lms/lms.git` if it’s not already done. A new directory called `lms` appears in your **project directory**. It contains the **Django project**, this project which references the **Django applications**.
2. Move into the `lms` project, optionally switch to another branch as indicated in [Install Koala LMS](#install-koala-lms) and install the **Koala LMS** dependencies: `pip3 install -r requirements.txt`
3. Before doing any migration, the [`SECRET_KEY`](https://docs.djangoproject.com/fr/2.2/ref/settings/#std:setting-SECRET_KEY) parameter must be set. You **MUST NOT** change the `lms/settings.py` file, as it contains settings for deployments of Koala LMS. Otherwise, for development purposes, you are encouraged to add a `lms/local_settings.py` file, where you can add more settings, like: `SECRET_KEY = "azertyuiop"` and of course, `DEBUG = True`.
4. Call `migrate` to create the database: `./manage.py migrate`
5. You can optionally load some fixtures, like the french ones: `./manage.py loaddata ./fixtures/sample-fr.json`

At this stage, your `lms/local_settings.py` file looks like:
```python
SECRET_KEY = "my very secret key"
DEBUG = True
```

And you can run the project with stable application versions (`accounts` and `learning`) using `./manage.py runserver`.

#### Load the demonstration user

If you intend to contribute to **Koala LMS**, it might be useful not to log manually each time you use Koala LMS. To avoid this, we provide, trough a [Django middleware](https://docs.djangoproject.com/en/2.2/topics/http/middleware/), a way to be automatically connected, when running a **demonstration server**.

In order to enable it, update the `lms/local_settings.py` file and add the following:
```python
DEMO = True  # To indicate the code is running as a demonstration
DEMONSTRATION_LOGIN = "erik-orsenna"  # A user that exists in the database (ie: in the fixtures) and that will be logged-in automatically
```

#### :prince: :princess: Create a super-user

A super user is useful when you want to access [**Django’s admin backend**](https://docs.djangoproject.com/en/2.2/ref/contrib/admin/). To create it, call `./manage.py createsuperuser` and fill the form with a username and a password.

### Run the development server

The development server can be run using the command line `./manage.py runserver`. Then, by default, a web-server will be started, listening to the port n°8000 on localhost. You can access it through [https://127.0.0.1:8000](https://127.0.0.1:8000).

### Contribute to a Koala LMS application

Now, you track stable applications that were installed in the **virtual environment** using `pip`. You can check [`learning`](https://pypi.org/project/django-koalalms-learning/) and [`accounts`](https://pypi.org/project/django-koalalms-accounts/) on [Pypi, the Python Package Repository](https://pypi.org/). If you wish to contribute to the `learning` application for instance, you **MUST NOT** download it in the `lms` directory, but in your workspace, the **project directory**. For more information on how applications work, please read [Applications](https://docs.djangoproject.com/en/2.2/ref/applications/) from the Django documentation.

1. Clone the Git repository `git clone https://gitlab.com/koala-lms/django-learning.git` into your **project directory**.
2. Create a symbolic link in the `lms` directory (**Koala LMS** project) to the `learning` package: `cd lms && ln -s ../django-learning/learning learning`. On Windows, `New-Item -ItemType SymbolicLink -Name learning -Target ..\django-learning\learning`.
3. Now, run the project, you’re using the code from the `master` or `develop` branch.

**NOTE**: you might need to refresh the dependencies in the virtual environment using `pip`, as new versions of applications may require extra dependencies.

# Getting Started

## :scroll: Submit a Patch or an Enhancement

Everything starts with a Gitlab issue. If you think something does not work properly, [open a new issue](https://gitlab.com/koala-lms/lms/issues/new) and **choose the appropriate **“Feature Proposal”** or **“Bug”** template. If you do not know which component you want to fix or enhance, just open an issue for the [Koala LMS project](https://gitlab.com/koala-lms/lms). We will sort issues after and move them to the appropriate project.

By contributing, you agree that your code will be published under the [GPLv3 licence](https://www.gnu.org/licenses/quick-guide-gplv3.html) and that you own what you write. Your other contributions (images, etc.) may be published under the [Creative Common Zero licence](https://creativecommons.org/publicdomain/zero/1.0/deed).

The process you should follow is :
1. Create **your own fork** of the code in Gitlab, or **clone** the repository locally.
2. Do the changes in your own repository. Remember that you are working on **only one feature** at a time. To do so, create a new branch called with the name of your feature, for instance: `git branch -d FEATURE`. **FIRST**, switch to the desired source branch. For instance, if you implement a bug fix, checkout to `master` first, if it’s an enhancement, checkout to `develop`. The source branch is important and depends on your modification.
3. Ensure your `user.name` and `user.email` are set to your real name and your real email address. Check the [Git documentation](https://git-scm.com/book/en/v2/Getting-Started-First-Time-Git-Setup) is order to do this.
4. Do the changes.
    * **Do commit** your changes only if your `HEAD` is in a stable state. This means, **do not commit** broken things or things that do not work. Before each commit, you should check most of the rules defined in [Code Review Process](#code-review-process)
    * **Commit only** the files related to your changes, please, use `git add ./path/to/filename` instead of `git add .` to understand what you are doing.
    * Your **commit message** must respect the template given below in [Commit Message Conventions](#commit-message-conventions).
    * It’s better if you [`sign-off`](https://git-scm.com/docs/git-commit) your commits using the `--signoff` option.
    * **DO NEVER** delete existing `migrations` file. Optionally, merge all your migrations into one file if it does make sense (one migrations for one “logical change”).
3. **Push your branch** to your own repository if you use Gitlab (or extract patches)
4. **Open a merge request** and ask for a merge from your branch to the **branch you used as basis** in step 2.
5. Your changes are being reviewed by a project maintainer. You can `push` and `force push` to your branch, files will be updated for the merge request.
6. Once your modification is accepted, your code is merged into the **source branch** you choose and **your source branch called `FEATURE` HAS TO BE DELETED**. Your must not work on it any longer.

* **Note**: please check the [5 best practices for using Git](https://deepsource.io/blog/git-best-practices/) if you’re not comfortable with it yet. And remember the rules
    * Make clean and single purpose commits.
    * Write meaningful commit messages (you might follow the [Commit Message Conventions](#commit-message-conventions) given below).
    * Commit early, commit often.
    * Don’t alter published history.
    * Don’t commit generated files, binary or artifacts.

### Continuing Developing

Let’s admit your patch was accepted and your source branch was deleted remotely. Your local branch still exists. In order to avoid issues, start by deleting it locally using `git branch -d FEATURE` and then ensure it has been remotely deleted using `git push --delete REMOTE FEATURE`. In this particular case, `REMOTE` should be `origin`. `origin` points to **YOUR REPOSITORY** in **YOUR NAMESPACE**.

`master` and `develop` branches **MUST NOT** be changed by you and should only track the official development. This makes things easier for future merges.

Once accepted into `develop` let’s say, **YOUR** version of `develop` is behind the official `develop` branch. You **MUST NOT** merge things yourself. Instead of this, you should pull the official `develop` branch locally and then push it to your remote project. Up to now, you have only one remote, `origin`. This is true if you only `git clone`’d the project. Go to your project, here `django-learning` and run:
```bash
$ git remote -v
origin  git@gitlab.com:NAMESPACE/django-learning.git (fetch)
origin  git@gitlab.com:NAMESPACE/django-learning.git (push)
```

You see that your `origin` remote refers to **your project** in **YOUR `NAMESPACE`**. Let’s add the official remote we will call let’s say, `koala_lms`:
```bash
$ git remote add koala_lms git@gitlab.com:koala-lms/django-learning.git
```

Now you see:
```bash
$ git remote -v
origin  git@gitlab.com:NAMESPACE/django-learning.git (fetch)
origin  git@gitlab.com:NAMESPACE/django-learning.git (push)
koala_lms  git@gitlab.com:koala-lms/django-learning.git (fetch)
koala_lms  git@gitlab.com:koala-lms/django-learning.git (push)
```

You can `fetch` all branches (`-a`) from the remote `koala_lms` and either `pull` them. For instance, first `checkout` to `develop` and pull from the official project:
```bash
# Switch to develop
$ git checkout develop
# Fetch all the changes from all the branches from koala_lms remote (official repository)
$ git fetch koala_lms -a
# Get the official develop branch from the official repository
$ git pull koala_lms develop
# Push the develop branch to YOUR PROJECT in YOUR NAMESPACE
$ git push origin develop
```

You **must not encounter any merge conflict** because you did not change anything in `develop`. Anyway, if the merge was accepted, you should see your commits if you call `git log`.

### TL;DR

Every time you start a new feature, update the source branch first, by pulling modifications from the official repository and then derive using `git branch`.

## :bug: How to report a bug

**If you find a security vulnerability, *SET the issue as confidential***. Please be as more precise as possible, and, if possible provide a fix for that vulnerability.

For any other case, please **choose the appropriate issue template**. Give us the following information:
* Which version of Django are you using? Which version of Python? On which OS?
* What did you do?
* What do you expect to see?
* What did you see instead?

## :gear: Code Review Process

If you implement a change (a bug fix or an enhancement) in Koala or any related application, you should ensure to follow the following rules:
* Minimize your code: this means remove the dead code, ensure you used [Bootstrap 4](https://getbootstrap.com/docs/4.0/getting-started/introduction/) instead of defining your own CSS classes if possible, try to optimize you code, factorize (remove any duplicates or copy/paste remains, etc). If you added a CSS class, let the `-` separator for Boostrap and instead use the `_`, as defined in [Snake Case](https://en.wikipedia.org/wiki/Snake_case).
* Your code must respect the [PEP 8 standards](https://www.python.org/dev/peps/pep-0008/) (with specific changes defined in `.editorconfig`). You can use [`prospector`](https://prospector.readthedocs.io/en/master/) to check that it’s done properly.
* Check for basic security issues using [`bandit`](https://bandit.readthedocs.io/en/latest/index.html).
* Write some [Django tests](https://docs.djangoproject.com/en/2.2/topics/testing/) (or any other relevant test) to validate your changes.
* Run all the tests, using `manage.py test APPLICATION_NAME`, `APPLICATION_NAME` possibly `learning` or `accounts`, in fact, the [Python Package](https://docs.python.org/3/tutorial/modules.html#packages) name.

A pipeline checks (in stage `test`) almost all those things, but it’s necessary to do this on your own before submitting anything. Once done, you are encouraged either to submit patches by email or by following the standard Gitlab merge request process.

## Commit Message Conventions

For the moment, we have few commit message requirements, but it’s better if your copy the following template and set Git accordingly.

First, copy and paste the following content in a file, for instance in your home directory, let’s call it `~/.git-commit-template.txt`. Once done, run the following Git command in your Git project:
`git config commit.template ~/.git-commit-template.txt`. Some extra information is given in the [Customizing Git Configuration documentation](https://git-scm.com/book/en/v2/Customizing-Git-Git-Configuration).

    # <type>: (If applied, this commit will...) <subject> (Max 50 char)
    # |<----  Using a Maximum Of 50 Characters  ---->|


    # Explain why this change is being made
    # |<----   Try To Limit Each Line to a Maximum Of 72 Characters   ---->|

    # Provide links or keys to any relevant tickets, articles or other resources
    # Example: Github issue #23

    # --- COMMIT END ---
    # Type can be
    #    feat     (new feature)
    #    fix      (bug fix)
    #    refactor (refactoring production code)
    #    style    (formatting, missing semi colons, etc; no code change)
    #    docs     (changes to documentation)
    #    test     (adding or refactoring tests; no production code change)
    #    chore    (updating grunt tasks etc; no production code change)
    #    l10n     (localization)
    #    i18n     (internationalization)
    # --------------------
    # Remember to
    #    Capitalize the subject line
    #    Use the imperative mood in the subject line
    #    Do not end the subject line with a period
    #    Separate subject from body with a blank line
    #    Use the body to explain what and why vs. how
    #    Can use multiple lines with "-" for bullet points in body
    # --------------------
    # For more information about this template, check out
    # https://gist.github.com/adeekshith/cd4c95a064977cdc6c50

## Labels

Below is the list of group labels as used in Koala LMS. Those labels are shared across projects.

* ~"Bug" `#FF0000`
* ~"Discussion" `#FFA500`
* ~"Documentation" `#004E00`
* ~"Enhancement" `#5CB85C`
* ~"Feature request" `#428BCA`
* ~"Help wanted" `#FFECBC`
* ~"Maintenance" `#0033CC`
* ~"Needs review" `#A295D6`
* ~"Newcomers" `#5843AD`
* ~"Question" `#D10069`
* ~"Support" `#F0AD4E`
* ~"Test" `#7F8C8D`
* ~"Test required" `#AD4363`
* ~"UX" `#AD8D43`
* ~"EPIC" `#663300`
* ~"Online demonstration" `#FFFF00`

#### Status

* ~"Status::Invalid" `#E4E669`
* ~"Status::In development" `#D1D100`
* ~"Status::Ready" `#004E00`
* ~"Status::Verified" `#69D100`

* ~"Status::Hold" `#D9534F`
* ~"Status::Wontfix" `#FFFFFF`

#### Priority

* ~"Priority::Low" `#0E8A16`
* ~"Priority::Medium" `#FBCA04`
* ~"Priority::High" `#D93F0B`
* ~"Priority::Critical" `#EE0701`

#### Board process

* ~"To Do" `#F0AD4E`
* ~"Doing" `#5CB85C`
* ~"Waiting for MR" `#5843AD`
