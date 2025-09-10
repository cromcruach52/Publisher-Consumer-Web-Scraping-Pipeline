const { connect } = require("mongodb") // Declare the connect variable
const db = connect("mongodb://localhost:27017/admin") // Declare the db variable
const articlesDB = db.getSiblingDB("articles_db")

// Create the articles_db database and a collection
articlesDB.createCollection("articles")

// Create an index on the url field for better performance
articlesDB.articles.createIndex({ url: 1 }, { unique: true })

print("MongoDB initialization completed for articles_db")
