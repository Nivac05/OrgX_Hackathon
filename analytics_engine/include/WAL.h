#pragma once
#include <string>
#include <fstream>
#include <mutex>
#include <vector>

struct LogEntry {
    std::string userId;
    std::string eventType;
    double probability;
};

class WriteAheadLog {
public:
    WriteAheadLog(const std::string& logFilePath);
    ~WriteAheadLog();

    // Append event before state mutation
    void append(const LogEntry& entry);
    
    // Crash-safe replay read
    std::vector<LogEntry> replay();

private:
    std::string filePath;
    std::mutex logMutex;
    std::ofstream outStream;
};
