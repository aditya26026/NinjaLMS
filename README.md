[![Koala LMS logo](static/lms/img/banner-sm.png)](https://www.koala-lms.org)

# :koala: Koala, Learning Management system

## :school: What is Koala LMS?

**Koala LMS** is a **Learning Management System** (*LMS*) that aims to be simple, **made by users**, **for users**. It has been originally developed in the [LORIA Laboratory](http://www.loria.fr/fr/), Nancy, France.

Contrary to other LMS like Moodle for instance, **Koala LMS** wants to stay **simple**, **user focused** and without useless functionalities. Features and requirements come from interviews of people from the [Université de Lorraine](https://www.univ-lorraine.fr/), Nancy, France.

A demonstration instance is available at [demo.koala-lms.org](https://demo.koala-lms.org). It is populated with sample data and refreshed every ten minutes (ie: 2:20; 2:30, etc.). Login as “Erik Orsenna” to access relevant data with the following credentials: `erik-orsenna` and `koala-lms` as the password. Up to now, the demonstration server is populated with data in french, coming from Wikipedia.

**Koala-LMS** components are free software (free as in freedom). All of them are distributed under the [**GPLv3 Licence**](https://www.gnu.org/licenses/quick-guide-gplv3.en.html). We want free code to **remain free**! :blush:

## Preamble

### Requirements

In order to make it easy to install **Koala LMS** on your system, we decided to use Python. Python is a **common and massively used language** in scientific and research communities. At the very early hours of the project, we hoped contributions from those communities. Thus, targeting a programming language well known by our community seems to be a great idea.

As you may know, **Django** is a super easy, extensible framework. Thanks to this approach, **Koala LMS** is distributed as Django applications that you can plug and make your very own **Learning Management system**! This way, **Koala LMS** is expandable or minimizable. The whole **Learning Management System** is, in fact a full project with all the applications enabled. If you want to do your very own installation, you can! Easy, uh?

### Technical requirements

**Koala LMS** and the components run with [**Django 2.2**](https://docs.djangoproject.com/en/2.2/releases/2.2/) and [**version 3.7**](https://www.python.org/downloads/release/python-370/). Only **long term support Django releases** will be supported in the future.

## :ship: Start using Docker

You need to [install `docker`](https://docs.docker.com/install/) on your system. We host the [docker image in the Gitlab Registry](https://gitlab.com/koala-lms/lms/container_registry). Its `Dockerfile` is located at [`./docker/stable/Dockerfile`](docker/stable/Dockerfile). You can get the image (*<50MB to download*) using:
```bash
docker pull registry.gitlab.com/koala-lms/lms
```

#### Tweak Docker deployment

You can tweak the `koala-lms` deployment using some environment variables. None is required.
* `LANGUAGE_CODE`: the Django corresponding setting.
* `TIME_ZONE`: the Django corresponding setting.
* `FIXTURE`: the fixture to load (relative to the project directory, ie: `./fixtures/sample.json`). You will find additional fixtures in the `fixtures` directory.
* `DEMO`: if you wish to enable the demonstration server
* `DEMONSTRATION_LOGIN`: the user that exists in the *fixture* that will be logged in
* `DEBUG`: whether to use Django debug mode.

#### Start the container

To run `koala-lms`. You just have to run:
```bash
docker run --name koala-lms -e FIXTURE="./fixtures/sample-fr.json" -e DEBUG=1 -p 8080:8080 registry.gitlab.com/koala-lms/lms
```
And the container will boot. The application is distributed under the URL [localhost:8080](http://localhost:8080).

## :open_hands: Contributing

Every kind of contribution is well welcomed! You can give us your feedback or report bugs. You can help us translate Koala-LMS components, write documentation, and more.

If you wish to contribute, please, follow the [contribution guidelines](CONTRIBUTING.md). It’s not that long, in a few minutes, you’ll understand how to help! :grinning:

## :book: Documentation

### :green_book: User documentation

We are not able to provide user documentation yet but we hope to have one really soon. If you wish to help us with this, please, read the [contribution guidelines](CONTRIBUTING.md).

### :ledger: Technical documentation

Technical documentation about **Koala LMS** is available in this [project wiki](https://gitlab.com/koala-lms/lms/wikis/home). As you have already understood, **Koala LMS** is a set of components and if you want to know more, please refer to each component documentation.

* the `learning` application is [`django-koalalms-learning`](https://pypi.org/project/django-koalalms-learning/) ([source code on Gitlab](https://gitlab.com/koala-lms/django-learning)).
* the `accounts` application is [`django-koalalms-accounts`](https://pypi.org/project/django-koalalms-accounts/) ([source code on Gitlab](https://gitlab.com/koala-lms/django-accounts)).
