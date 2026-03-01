#include "Inference.h"
#include <fstream>
#include <iostream>
#include <cmath>
#include <numeric>

InferenceEngine::InferenceEngine(const std::string& modelPath) {
    loadModel(modelPath);
}

void InferenceEngine::loadModel(const std::string& path) {
    std::ifstream file(path);
    if (!file.is_open()) {
        std::cerr << "Failed to read model JSON: " << path << std::endl;
        return;
    }
    
    try {
        json j;
        file >> j;
        
        // Assuming model structure based on prompt requirement: logistic_regression_model.json
        if (j.contains("weights")) {
            for (auto& w : j["weights"]) weights.push_back(w.get<double>());
        }
        if (j.contains("bias")) {
            bias = j["bias"].get<double>();
        }
        
        // Define an arbitrary feature map mapping typical analytics events to the weight vector indices
        featureMap["login"] = 0;
        featureMap["click"] = 1;
        featureMap["scroll"] = 2;
        featureMap["checkout"] = 3;
        
    } catch (const std::exception& e) {
        std::cerr << "JSON Exception: " << e.what() << std::endl;
    }
}

// Convert event history into a feature vector matching the weight dimensions
std::vector<double> InferenceEngine::extractFeatures(const std::vector<std::string>& events) {
    std::vector<double> features(weights.size(), 0.0);
    
    // Simple naive frequency count for feature extraction
    for (const auto& ev : events) {
        auto it = featureMap.find(ev);
        if (it != featureMap.end() && it->second < features.size()) {
            features[it->second] += 1.0; 
        }
    }
    return features;
}

double InferenceEngine::sigmoid(double x) {
    return 1.0 / (1.0 + std::exp(-x));
}

double InferenceEngine::getProbability(const std::string& userId, const std::vector<std::string>& recentEvents) {
    if (weights.empty()) return 0.0;
    
    std::vector<double> features = extractFeatures(recentEvents);
    
    double z = bias;
    for (size_t i = 0; i < weights.size(); ++i) {
        z += weights[i] * features[i];
    }
    
    return sigmoid(z);
}
