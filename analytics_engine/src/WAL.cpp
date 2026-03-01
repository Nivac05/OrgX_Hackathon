#include "WAL.h"
#include <iostream>
#include <sstream>

WriteAheadLog::WriteAheadLog(const std::string& logFilePath) 
    : filePath(logFilePath) {
    // Open in append mode
    outStream.open(filePath, std::ios_base::app);
    if (!outStream.is_open()) {
        std::cerr << "Failed to open WAL file: " << filePath << std::endl;
    }
}

WriteAheadLog::~WriteAheadLog() {
    if (outStream.is_open()) {
        outStream.close();
    }
}

void WriteAheadLog::append(const LogEntry& entry) {
    std::lock_guard<std::mutex> lock(logMutex);
    if (outStream.is_open()) {
        outStream << entry.userId << "," << entry.eventType << "," << entry.probability << "\n";
        outStream.flush(); // Ensure it hits the disk immediately for crash safety
    }
}

std::vector<LogEntry> WriteAheadLog::replay() {
    std::lock_guard<std::mutex> lock(logMutex);
    std::vector<LogEntry> entries;
    std::ifstream inStream(filePath);
    
    if (!inStream.is_open()) {
        return entries;
    }

    std::string line;
    while (std::getline(inStream, line)) {
        std::stringstream ss(line);
        std::string userId, eventType, probStr;
        
        if (std::getline(ss, userId, ',') &&
            std::getline(ss, eventType, ',') &&
            std::getline(ss, probStr)) {
            
            try {
                double prob = std::stod(probStr);
                entries.push_back({userId, eventType, prob});
            } catch (...) {
                // Ignore malformed lines during crash recovery
            }
        }
    }
    return entries;
}
