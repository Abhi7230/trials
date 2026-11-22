# Machine Learning Fundamentals

## What is Machine Learning?

Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. It focuses on developing computer programs that can access data and use it to learn for themselves.

## Types of Machine Learning

### Supervised Learning

In supervised learning, the algorithm learns from labeled training data. The model makes predictions based on input data and receives corrective feedback to adjust its parameters.

Common algorithms include:
- Linear Regression
- Logistic Regression
- Decision Trees
- Support Vector Machines
- Neural Networks

### Unsupervised Learning

Unsupervised learning works with unlabeled data. The system tries to learn patterns and structures from the input without explicit guidance.

Examples include:
- K-means clustering
- Hierarchical clustering
- Principal Component Analysis (PCA)
- Autoencoders

### Reinforcement Learning

Reinforcement learning involves an agent learning to make decisions by performing actions and receiving rewards or penalties. The goal is to maximize cumulative reward over time.

## Model Evaluation

### Training and Testing

Data is typically split into training and test sets. The model learns from training data and is evaluated on unseen test data to measure generalization.

### Metrics

Common evaluation metrics include:
- Accuracy: Proportion of correct predictions
- Precision: True positives / (True positives + False positives)
- Recall: True positives / (True positives + False negatives)
- F1 Score: Harmonic mean of precision and recall

## Overfitting and Underfitting

Overfitting occurs when a model learns the training data too well, including noise and outliers. Underfitting happens when the model is too simple to capture underlying patterns.

Regularization techniques like L1 and L2 help prevent overfitting by adding penalty terms to the loss function.
