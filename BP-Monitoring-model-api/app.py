from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS
import joblib
from preprocessing import preprocess_json_data
from preprocessing import EnsembleModel

app = Flask(__name__)

# Enable CORS for the app (allow all domains, or specify the domain)
CORS(app)  # This allows all domains to access the Flask API
# You can restrict to specific origins like:
#CORS(app, origins=["http://localhost:3000"])  # For example, if your frontend is on localhost:3000

# Load the trained model
model = joblib.load('random_forest_tuned_model.pkl')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get JSON data from the incoming request
        json_data = request.get_json()
        
        # Print the raw input data (for debugging purposes)
        print("Input JSON Data:", json_data)

        # Preprocess the incoming data and get the features (X)
        features = preprocess_json_data(json_data)
        
        # Print the preprocessed features (for debugging purposes)
        print("Preprocessed Features:", features)

        # Make predictions using the preprocessed features (X)
        prediction = model.predict(features)

        # Print the prediction (for debugging purposes)
        print("Prediction:", prediction)

        # Return the prediction as a JSON response
        return jsonify({'prediction': prediction.tolist()})

    except Exception as e:
        print(f"Error: {str(e)}")  # Print the error if it occurs
        return jsonify({'error': str(e)}), 500

#if __name__ == '__main__':
 #   app.run(debug=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=7860)  # Change the port to 7860
