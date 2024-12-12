import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt
import joblib
import numpy as np  # For generating random seeds

# Load data from CSV
data = pd.read_csv("feeds.csv")

# Apply a moving average to reduce noise
window_size = 5  # Adjust the window size as needed
data["field3"] = data["field3"].rolling(window=window_size, min_periods=1).mean()
data["field4"] = data["field4"].rolling(window=window_size, min_periods=1).mean()

# Extract features and target
X = data[["field3", "field4"]]  # Hand and forearm EMG
y = data["field1"]              # Classification: 1=crimp, 0=drag

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Initialize lists to store accuracies and seeds
n_estimators_range = range(10, 310, 10)  # Test n_estimators from 10 to 300 in steps of 10
training_accuracies = []
validation_accuracies = []
seeds = []  # To store the seeds for each iteration

# Loop over n_estimators
for n in n_estimators_range:
    # Generate a random seed
    seed = np.random.randint(0, 10000)
    seeds.append(seed)
    
    # Train a RandomForestClassifier with the current n_estimators and seed
    clf = RandomForestClassifier(n_estimators=n, random_state=seed)
    clf.fit(X_train, y_train)

    # Calculate training accuracy
    train_acc = accuracy_score(y_train, clf.predict(X_train))
    training_accuracies.append(train_acc)

    # Calculate validation accuracy
    val_acc = accuracy_score(y_test, clf.predict(X_test))
    validation_accuracies.append(val_acc)

# Plot the results
plt.figure(figsize=(10, 6))
plt.plot(n_estimators_range, training_accuracies, label="Training Accuracy", marker='o')
plt.plot(n_estimators_range, validation_accuracies, label="Validation Accuracy", marker='o')
plt.axvline(n_estimators_range[validation_accuracies.index(max(validation_accuracies))],
            color='r', linestyle='--', label="Optimal n_estimators")
plt.title("Effect of n_estimators on Model Performance")
plt.xlabel("Number of Trees (n_estimators)")
plt.ylabel("Accuracy")
plt.legend()
plt.grid()
plt.show()

# Find the optimal number of trees and the corresponding seed
optimal_idx = validation_accuracies.index(max(validation_accuracies))
optimal_n = n_estimators_range[optimal_idx]
optimal_seed = seeds[optimal_idx]

print(f"Optimal n_estimators: {optimal_n}")
print(f"Validation accuracy at optimal n_estimators: {max(validation_accuracies):.2f}")
print(f"Random seed for optimal n_estimators: {optimal_seed}")

# Retrain the model with the optimal n_estimators and seed
print("Retraining the model with the optimal number of trees...")
final_model = RandomForestClassifier(n_estimators=optimal_n, random_state=optimal_seed)
final_model.fit(X_train, y_train)

# Save the trained model
joblib.dump(final_model, "optimized_emg_classifier.pkl")
print("Optimized model saved as optimized_emg_classifier.pkl")
