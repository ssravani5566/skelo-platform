"""Built-in syllabi used when a student chooses a course not hosted in SKelo."""

COURSE_TOPICS = {
    "python": [
        ("Python setup and fundamentals", "Install Python, use the interpreter, and understand the structure of a program."),
        ("Variables, data types and operators", "Work with strings, numbers, booleans, collections and expressions."),
        ("Conditions and loops", "Build decisions and repeat work with if/elif, for and while."),
        ("Functions and modules", "Write reusable functions, imports, packages and clean modules."),
        ("Lists, tuples, sets and dictionaries", "Choose the right collection and manipulate data confidently."),
        ("Strings, files and exceptions", "Process text, read/write files and handle errors safely."),
        ("Object-oriented Python", "Practice classes, objects, inheritance, composition and properties."),
        ("Libraries and practical scripting", "Use the standard library and build small automation scripts."),
        ("Testing and debugging", "Trace bugs, write unit tests and improve code quality."),
        ("Python mini project and revision", "Build a small application and review the key concepts."),
    ],
    "java": [
        ("Java setup and syntax", "Set up the JDK and write your first Java programs."),
        ("Variables, types and operators", "Understand primitive types, casting and expressions."),
        ("Conditions, loops and arrays", "Control program flow and process collections of values."),
        ("Methods and object-oriented basics", "Create methods, classes, objects and constructors."),
        ("Inheritance, interfaces and polymorphism", "Model reusable designs with core OOP principles."),
        ("Collections and generics", "Use List, Set, Map and generic types."),
        ("Exceptions, files and streams", "Handle errors and work with file input/output."),
        ("Java modern features", "Explore lambdas, streams and common utility APIs."),
        ("Testing and debugging", "Debug applications and write focused tests."),
        ("Java mini project and revision", "Build a console or simple desktop application."),
    ],
    "javascript": [
        ("JavaScript foundations", "Understand syntax, variables, values and operators."),
        ("Conditions, loops and functions", "Build program flow and reusable functions."),
        ("Arrays, objects and modern JavaScript", "Transform data using array methods, objects and ES modules."),
        ("DOM and browser events", "Update web pages and respond to user interactions."),
        ("Asynchronous JavaScript", "Use promises, async/await and fetch APIs."),
        ("Error handling and debugging", "Inspect runtime behavior and handle failures."),
        ("Working with APIs", "Consume REST endpoints and process JSON data."),
        ("JavaScript project and revision", "Build an interactive browser application."),
    ],
    "react": [
        ("React and modern JavaScript setup", "Set up a React project and understand its file structure."),
        ("Components, JSX and props", "Build reusable UI components and pass data between them."),
        ("State and event handling", "Create interactive interfaces with component state."),
        ("Hooks and effects", "Use useState, useEffect, useMemo and custom hooks."),
        ("Forms and validation", "Build accessible forms and validate user input."),
        ("Routing and page layouts", "Create multi-page experiences with React Router."),
        ("API integration", "Connect React to backend APIs and handle loading/error states."),
        ("Performance and component design", "Structure components and avoid unnecessary rendering."),
        ("React capstone project", "Build and review a complete responsive application."),
    ],
    "sql": [
        ("Database concepts and SQL setup", "Understand tables, rows, keys and relational databases."),
        ("SELECT, filtering and sorting", "Retrieve data using WHERE, ORDER BY and limiting."),
        ("Aggregate functions and grouping", "Summarize data with COUNT, SUM, AVG and GROUP BY."),
        ("Joins and relationships", "Combine related tables with INNER, LEFT and other joins."),
        ("Subqueries and common table expressions", "Solve multi-step queries with nested queries and CTEs."),
        ("Insert, update and delete", "Safely modify records and use transactions."),
        ("Indexes, constraints and normalization", "Design reliable schemas and improve query performance."),
        ("SQL practice project and revision", "Analyze a sample dataset and review important patterns."),
    ],
    "data science": [
        ("Data science workflow and statistics", "Understand datasets, questions, sampling and descriptive statistics."),
        ("Python for data analysis", "Work with NumPy and pandas for data manipulation."),
        ("Data cleaning and preparation", "Handle missing values, duplicates and inconsistent records."),
        ("Exploratory data analysis", "Discover patterns and summarize findings."),
        ("Data visualization", "Communicate insights with clear charts and dashboards."),
        ("Probability and statistical inference", "Apply distributions, hypothesis tests and confidence intervals."),
        ("Introductory machine learning", "Train and evaluate baseline predictive models."),
        ("Data science capstone", "Complete an end-to-end analysis and present conclusions."),
    ],
    "machine learning": [
        ("Machine learning foundations", "Understand supervised, unsupervised and reinforcement learning."),
        ("Data preparation and feature engineering", "Prepare datasets and create useful model features."),
        ("Regression models", "Build and evaluate regression algorithms."),
        ("Classification models", "Train classifiers and interpret performance metrics."),
        ("Clustering and dimensionality reduction", "Explore unsupervised learning techniques."),
        ("Model validation and tuning", "Use cross-validation and tune hyperparameters."),
        ("Model deployment basics", "Package a model and expose a simple prediction interface."),
        ("Machine learning mini project", "Complete a small supervised or unsupervised project."),
    ],
    "artificial intelligence": [
        ("AI foundations and responsible use", "Learn AI concepts, problem types, limitations and responsible practice."),
        ("Search and problem solving", "Explore state-space search, heuristics and planning."),
        ("Knowledge representation", "Represent facts, rules and relationships."),
        ("Machine learning overview", "Understand how systems learn patterns from data."),
        ("Neural networks basics", "Explore layers, activation functions and training."),
        ("Generative AI and language models", "Understand prompts, tokens, context and model behavior."),
        ("AI applications and evaluation", "Evaluate quality, privacy, bias and reliability."),
        ("AI mini project and revision", "Design a small responsible AI-powered workflow."),
    ],
    "dsa": [
        ("Complexity analysis and problem solving", "Understand Big-O time and space complexity."),
        ("Arrays, strings and hashing", "Solve common lookup, frequency and two-pointer problems."),
        ("Linked lists, stacks and queues", "Implement linear data structures and their operations."),
        ("Sorting and searching", "Practice binary search and essential sorting algorithms."),
        ("Trees and binary search trees", "Traverse, search and update tree structures."),
        ("Heaps, graphs and traversal", "Use priority queues, BFS and DFS."),
        ("Greedy and dynamic programming", "Recognize patterns and solve optimization problems."),
        ("Timed practice and revision", "Solve mixed interview-style problems and review mistakes."),
    ],
    "html": [
        ("Web foundations and semantic HTML", "Understand page structure and accessible HTML elements."),
        ("Forms, tables and media", "Build useful content and input experiences."),
        ("CSS selectors and box model", "Style elements and understand layout fundamentals."),
        ("Flexbox and Grid", "Create responsive page layouts."),
        ("Typography, color and visual hierarchy", "Build consistent, readable interfaces."),
        ("Responsive design and accessibility", "Adapt layouts to devices and improve usability."),
        ("HTML/CSS mini project", "Create and refine a responsive web page."),
    ],
    "django": [
        ("Python web and Django foundations", "Understand request/response flow and create a Django project."),
        ("URLs, views and templates", "Build pages and route user requests."),
        ("Models and ORM", "Design database models and query data."),
        ("Forms, validation and authentication", "Accept input and protect account workflows."),
        ("Admin, static files and media", "Manage content and serve application assets."),
        ("Django REST Framework", "Create serializers, API views and endpoints."),
        ("Testing, security and deployment", "Test endpoints and prepare a secure deployment."),
        ("Django capstone project", "Build a small full-stack application."),
    ],
    "cybersecurity": [
        ("Security foundations and ethics", "Learn core security principles, scope and legal boundaries."),
        ("Networking and operating system basics", "Understand networks, services, permissions and logs."),
        ("Threats, vulnerabilities and risk", "Identify common threats and assess impact."),
        ("Web application security", "Study common web risks and defensive controls."),
        ("Identity, access and cryptography", "Learn authentication, authorization and encryption basics."),
        ("Monitoring and incident response", "Read security events and outline response steps."),
        ("Secure development practices", "Apply validation, patching and least privilege."),
        ("Security review and revision", "Review defensive controls using a safe lab scenario."),
    ],
    "cloud": [
        ("Cloud computing foundations", "Understand service models, regions and shared responsibility."),
        ("Compute, storage and networking", "Explore core cloud building blocks."),
        ("Identity and access management", "Apply roles, policies and least privilege."),
        ("Databases and managed services", "Choose appropriate managed data services."),
        ("Monitoring, reliability and scaling", "Understand metrics, availability and autoscaling."),
        ("Security, cost and governance", "Plan safe access and cost-aware usage."),
        ("Cloud deployment mini project", "Deploy a small application and document the architecture."),
    ],
}

GENERIC_TOPICS = [
    ("Foundations and learning roadmap", "Understand the subject, prerequisites and the skills you will build."),
    ("Core concepts and terminology", "Learn the essential ideas, vocabulary and mental models."),
    ("Tools, setup and basic workflow", "Set up the tools and practice the standard workflow."),
    ("Fundamental techniques", "Practice the most frequently used techniques step by step."),
    ("Guided exercises", "Apply the concepts with small examples and guided practice."),
    ("Intermediate concepts", "Connect foundational ideas and solve more involved tasks."),
    ("Practical application", "Use the knowledge in a realistic scenario or case study."),
    ("Mini project", "Create a small project that demonstrates the skills learned."),
    ("Review and knowledge consolidation", "Review difficult areas, summarize notes and revisit mistakes."),
    ("Final practice and next steps", "Complete a final practice task and identify what to learn next."),
]

def topics_for_course(title):
    normalized = (title or "").strip().lower()
    # More specific groups are checked before broad keyword matches.
    ordered = ["machine learning", "data science", "artificial intelligence", "cybersecurity", "django", "javascript", "react", "python", "java", "sql", "dsa", "html", "cloud"]
    for key in ordered:
        if key in normalized:
            return COURSE_TOPICS[key]
    if any(term in normalized for term in ("data structure", "algorithm", "dsa")):
        return COURSE_TOPICS["dsa"]
    if any(term in normalized for term in ("aws", "azure", "cloud")):
        return COURSE_TOPICS["cloud"]
    if any(term in normalized for term in ("gen ai", "generative ai", "deep learning", "nlp")):
        return COURSE_TOPICS["artificial intelligence"]
    return GENERIC_TOPICS
