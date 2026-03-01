#pragma once

#include <unordered_map>
#include <string>
#include <shared_mutex>
#include <vector>

struct UserState {
    int eventCount = 0;
    double lastProbability = 0.0;
    std::vector<std::string> recentEvents;
    bool isSuspicious = false;
};

// Fine-grained bucket locking implementation
class KVStore {
public:
    KVStore(size_t numBuckets = 16);
    
    void updateUserState(const std::string& userId, const std::string& event, double probability);
    UserState getUserState(const std::string& userId);
    
    std::vector<std::string> getSuspiciousUsers();
    size_t getTotalUsers();

private:
    struct Bucket {
        std::unordered_map<std::string, UserState> map;
        mutable std::shared_mutex mutex;
    };

    std::vector<Bucket> buckets;
    
    size_t getBucketIndex(const std::string& key) const;
};
