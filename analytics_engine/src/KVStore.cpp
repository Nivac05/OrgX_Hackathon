#include "KVStore.h"
#include <functional>

KVStore::KVStore(size_t numBuckets) : buckets(numBuckets) {}

size_t KVStore::getBucketIndex(const std::string& key) const {
    return std::hash<std::string>{}(key) % buckets.size();
}

void KVStore::updateUserState(const std::string& userId, const std::string& event, double probability) {
    size_t idx = getBucketIndex(userId);
    std::unique_lock<std::shared_mutex> lock(buckets[idx].mutex);
    
    auto& state = buckets[idx].map[userId];
    state.eventCount++;
    state.lastProbability = probability;
    state.recentEvents.push_back(event);
    
    // Simple naive threshold for suspicion definition
    if (probability > 0.8 || state.eventCount > 100) {
        state.isSuspicious = true;
    }
}

UserState KVStore::getUserState(const std::string& userId) {
    size_t idx = getBucketIndex(userId);
    std::shared_lock<std::shared_mutex> lock(buckets[idx].mutex);
    
    auto it = buckets[idx].map.find(userId);
    if (it != buckets[idx].map.end()) {
        return it->second;
    }
    return UserState{};
}

std::vector<std::string> KVStore::getSuspiciousUsers() {
    std::vector<std::string> suspicious;
    for (const auto& bucket : buckets) {
        std::shared_lock<std::shared_mutex> lock(bucket.mutex);
        for (const auto& pair : bucket.map) {
            if (pair.second.isSuspicious) {
                suspicious.push_back(pair.first);
            }
        }
    }
    return suspicious;
}

size_t KVStore::getTotalUsers() {
    size_t total = 0;
    for (const auto& bucket : buckets) {
        std::shared_lock<std::shared_mutex> lock(bucket.mutex);
        total += bucket.map.size();
    }
    return total;
}
