# Capstone Design Project Management

## Introduction

This Computer Science Capstone project is sponsored by Dr. Monica Anderson Herzog. The purpose of this project is to create a platform for Dr. Anderson to manage new and ongoing senior design projects.

Read more on this project's [Github Pages](https://jmburke4.github.io/capstone-design-manager/).

## Setup

    If on Windows, use a Unix-like terminal (Such as Cygwin)

1. Create environment files

    The ```docker-compose.yml``` scripts require valid ```.env``` and ```.env.db``` files to be in the root directory. See ```env.example``` and ```env.example.db``` for ```.env``` file examples. The default naming conventions for this repositories development environment are ```docker-compose.dev.yml```, ```.env.dev```, and ```.env.deb.db```. In these files you must configure a default username, password, and default database name.

    > Never commit your own development or production environment files to keep secrets protected.

2. Start the Docker engine on your machine

3. Build containers

    > Specify a compose script with ```docker-compose -f <compose script name>```

     ```docker-compose -f <compose script> build```
4. Start containers

    ```docker-compose -f <compose script> up```
5. Run migrations

    ```docker-compose -f <compose script> exec backend python manage.py migrate --noinput```

    > If you have added new models or a new app, run ```docker-compose -f <compose script> exec backend python manage.py makemigrations``` before running the migrate command

6. Create Admin User

    ```docker-compose -f <compose script> exec backend python manage.py createsuperuser ```

    > Setting up an admin will allow you to log in to the Django admin page.

7. Stop containers

    ```docker-compose -f <compose script> stop```

## Repository Structure

## Docker Commands

| Command | Description |
|--|--|
|```docker-compose build```| Builds an image using the docker-compose.yml in the cwd |
|```docker-compose up -d```| Starts a container from the build image(s), ```-d``` detaches the process from your terminal |
|```docker-compose up -d --build```| Starts containers after rebuilding them |
|```docker-compose stop```| Stops the running containers |
|```docker-compose down -v```| Stops running containers and removes them, ```-v``` also removes volumes |
|```docker-compose exec <service> <command>```| Execute a command inside the specified container |

Quick psql [reference](google.com/search?smstk=ChhCWU5MUDBsODdkNUFLM3BaK1hxRnpvdz0QBA%3D%3D&smstidx=0&q=quick+and+dirty+psql+commands&udm=50&csuir=1&aep=34&kgs=9e62baadf59f9e95&shem=bdsle,epsdc&shndl=37&shmd=H4sIAAAAAAAA_3WNOw7CMBAFSZsjICG5RiImDQXiLtbGttYr4k92HQWOR8upMDWinac307-6_rCsZO8KklOOuD5VkWVWNsfYkOxvodYiV623bRtQKlSyQ1u1eGAbToVzzBooGgnA3tSwxikBzUNJeNy9O_NPQBHQi564dSihxpxx9miQwZFPVY-PH2baPzlgZ8bL2ZVv4wMhIaRZxAAAAA&shmds=v1_ATWGeePY93TdMuXM0BfH7IdnnF4SioeAjgHOXkjlgJovPO_njw&source=sh/x/aio/m1/1)


## Setting Up Oauth (Shared dev tenant)

- **Auth0 Tenant:** `dev-qjyd077ykn3qqq7v.us.auth0.com`
- **Client ID:** `WMPr5zJLNFI0j9A8iUymDfAsP2mUXsn3`
- **API Identifier:** `https://backend-api-capstone/`

Instructions:
1. Perform clean build (You may need to remove/delete cotainers and volumes. This is easily done via the docker desktop GUI dashboard or CLI.)
2. Copy and paste the following values int /.env.dev **AND** /frontend/.env.local (if /frontend/.env.local dne, create it and add the env variables):

    AUTH0_DOMAIN=dev-qjyd077ykn3qqq7v.us.auth0.com
    AUTH0_CLIENT_ID=WMPr5zJLNFI0j9A8iUymDfAsP2mUXsn3
    AUTH0_AUDIENCE=https://backend-api-capstone/

For the .env.dev.local in the frontend directory, you will need to add the prefix 'VITE_' to each of the variables like:
    
    VITE_AUTH0_DOMAIN=dev-qjyd077ykn3qqq7v.us.auth0.com
    VITE_AUTH0_CLIENT_ID=WMPr5zJLNFI0j9A8iUymDfAsP2mUXsn3
    VITE_AUTH0_AUDIENCE=https://backend-api-capstone/

(These are front public variables, and it is fine to include them in the readme and upload to the repo. These values are subject to change.)


## Creating App Users

Once the project is built and deployed with Auth0 correctly configured, a user will need to create an account to access the app.

Assuming the user has navigated to the landing page of the app, they will see two options: 

- **Log In**
- **Sign Up**

A first-time user must select "Sign Up." They will then be prompted with two options:

- **I am a Student**
- **I am a Sponsor**

If the user is a student in the capstone class, they should select "I am a Student." Upon doing so, they will be navigated to the Auth0 signup page, where the following restrictions will be applied:

- **The user will only be able to sign up using an email with the @crimson.ua.edu domain**
- **The user will only be able to use the 'email-password' sign-in option, as they are restricted to Crimson emails and MySSO has yet to be configured.**
- **Upon signing up, Auth0 will send a verification email to the email used when signing up. Only after verifying their email will the user be able to log in to the app with their new account.**
- **If the user signs up with a Crimson email that does not exist in the student table in the PostgreSQL database, they will not be fed an error message and will only be able to log out. This is to prevent students who are not in the capstone class from using the app.**

If the user is a sponsor, they should select "I am a Sponsor." Doing so will navigate them to the Auth0 signup page. For sponsors, social logins (such as Google SSO) will be available. If the sponsor signs up with the 'email-password' option, they must complete the email verification before being granted access to the app. Currently, there is no option to resend the verification email, and Auth0 Email Authentication links expire after 7 days. In future development, an option to resend the verification link would be a valuable feature.

The sign-up process is fragile, and there will be ways to confuse the role-assignment operation that occurs when a user navigates from the app sign-up page to the Auth0 client. Effectively, the intended designed flow goes as follows:

- **User selects sign up as either sponsor or student"**
- **User is redirected to the Auth0 signup page, and their role is passed as a hint**
- **The Auth0 action scripts trigger and handle the user based on their role, erroring if their role is obfuscated**
- **When creating a user, Auth0 uses the hint and assigns role metadata to the new account according to it**
- **Upon subsequent logins with the new account, the metadata will be referenced and passed to the App in order to direct the user to their correct landing page**

It is highly likely that the current implementation is vulnerable to role spoofing/privilege escalation. However, given the current nature of the app, this does not pose a severe threat but only a potentially severe annoyance for the admin.
