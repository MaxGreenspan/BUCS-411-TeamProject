For the backend, we have considered the following two:

1. Express (javascript)
2. Python Flask.

We decided to choose python flask, because:
  The APIs we chose are chatgpt api and the openai DALL-E image generation api. They have a python library which makes api calls easier to make.
  Express doesn't have an official library.
   Python flask has a module called flask-login. It can handle the user login easier and nicer. These are important features of our apps, and flask serves them just well.
 Also, python have flask-mysql, which makes CRUD from our database easier to implement.
 
 We chose relational because in the early design of the project, we thought we may use some join operation(retrieve history records based on user email). Also, data should be structured. It is hard to do join in NoSQL database,
 and it makes more sense for us to use a relational database if the data have to be structured.
 

 We decided to use the Jinja template python flask over react. First, it is enough for the complexity of our front end. Second, it is easier to do.
 
 We still have to learn some python flask, but that seems doable given the time left for the project.
