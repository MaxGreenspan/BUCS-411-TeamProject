For the backend, we have considered the following two:

1. Express (javascript)
2. Python Flask.

We decided to choose Python Flask, because:
  The APIs we chose are chatgpt api and the openai DALL-E image generation api. They have a python library which makes it easier to make api calls.
  Express doesn't have an official library for those apis.
   Python flask has a module called flask-login. It can handle the user login more efficiently. These are important features of our app, and flask serves them just well.
 Also, python has flask-mysql, which makes CRUD from our database easier to implement.
 Additionally, for python, we first found the authlib package that can make OAuth easier. Although passport is available for other languages, for the reasons stated above we have elected to use python.
 
 For the database:
 
 We chose relational because in the early design of the project, we thought we may use some join operations. Also, data should be structured since we are only storing certain attributes and we will not have different attributes for different records. It is difficult to do "join" in a NoSQL database,
 and it therefore makes more practical sense for us to use a relational database since the data has to be structured.
 
 
 For rendering front end:
 
 We decided to use the Jinja template python flask over react. First, it is enough for the complexity of our front end. Second, it is easier to execute. Given the team members are busy in the summer, it makes more sense to use render_template from flask.
 
 
 We still have to learn some python flask and about templating html, but that seems doable given the time left for the project.
