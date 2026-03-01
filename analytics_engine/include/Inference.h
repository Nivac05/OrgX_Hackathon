#pragma once

#include <string>
#include <vector>
#include <unordered_map>
#include "nlohmann/json.hpp"

using json = nlohmann::json;

class InferenceEngine {
public:
    InferenceEngine(const std::string& modelPath);
    
    // Calculates logistic regression probability based on user state history
    double getProbability(const std::string& userId, const std::vector<std::string>& recentEvents);

private:
    std::vector<double> weights;
    double bias;
    
    // Feature extraction maps an event type to a feature index
    std::unordered_map<std::string, int> featureMap;
    
    void loadModel(const std::string& path);
    std::vector<double> extractFeatures(const std::vector<std::string>& events);
    double sigmoid(double x);
};
