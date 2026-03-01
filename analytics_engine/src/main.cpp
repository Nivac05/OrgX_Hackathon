#include "Inference.h"
#include "KVStore.h"
#include "ThreadPool.h"
#include "WAL.h"
#include "httplib.h"
#include <iostream>
#include <memory>
#include <sstream>


int main() {
  httplib::Server svr;

  // Load components
  std::cout << "Starting Behavioural Analytics Engine (using httplib)..."
            << std::endl;

  auto modelEngine =
      std::make_shared<InferenceEngine>("../../logistic_regression_model.json");
  auto kvStore = std::make_shared<KVStore>();
  auto wal = std::make_shared<WriteAheadLog>("events_wal.log");

  // Recovery
  auto recoveredEntries = wal->replay();
  for (const auto &entry : recoveredEntries) {
    kvStore->updateUserState(entry.userId, entry.eventType, entry.probability);
  }
  std::cout << "Recovered " << recoveredEntries.size() << " entries from WAL."
            << std::endl;

  auto threadPool = std::make_shared<ThreadPool>(4);

  // POST /event
  svr.Post("/event", [modelEngine, kvStore, wal, threadPool](
                         const httplib::Request &req, httplib::Response &res) {
    // Very basic manual JSON parsing to avoid heavy dependencies errors in
    // GCC 6.3 In real app, we use nlohmann_json, but let's see if we can do
    // basic extraction if nlohmann/json works, we'll use it.

    try {
      auto jsonReq = nlohmann::json::parse(req.body);
      std::string userId = jsonReq["user_id"];
      std::string eventType = jsonReq["event_type"];

      auto future =
          threadPool->enqueue([userId, eventType, modelEngine, kvStore, wal] {
            auto state = kvStore->getUserState(userId);
            std::vector<std::string> recent = state.recentEvents;
            recent.push_back(eventType);

            double prob = modelEngine->getProbability(userId, recent);
            wal->append({userId, eventType, prob});
            kvStore->updateUserState(userId, eventType, prob);
            return prob;
          });

      double prob = future.get();

      nlohmann::json response;
      response["status"] = "success";
      response["bot_probability"] = prob;
      res.set_content(response.dump(), "application/json");
    } catch (...) {
      res.status = 400;
      res.set_content("Invalid JSON", "text/plain");
    }
  });

  // GET /user/:id
  svr.Get(R"(/user/([^/]+))",
          [kvStore](const httplib::Request &req, httplib::Response &res) {
            std::string userId = req.matches[1];
            auto state = kvStore->getUserState(userId);

            nlohmann::json response;
            response["user_id"] = userId;
            response["event_count"] = state.eventCount;
            response["last_probability"] = state.lastProbability;
            response["is_suspicious"] = state.isSuspicious;
            res.set_content(response.dump(), "application/json");
          });

  // GET /metrics
  svr.Get("/metrics", [kvStore, threadPool](const httplib::Request &req,
                                            httplib::Response &res) {
    nlohmann::json response;
    response["total_users"] = kvStore->getTotalUsers();
    response["working_threads"] = threadPool->getWorkingThreads();
    res.set_content(response.dump(), "application/json");
  });

  // GET /suspicious
  svr.Get("/suspicious",
          [kvStore](const httplib::Request &req, httplib::Response &res) {
            auto badActors = kvStore->getSuspiciousUsers();
            nlohmann::json response;
            response["suspicious_count"] = badActors.size();
            response["users"] = badActors;
            res.set_content(response.dump(), "application/json");
          });

  // Handle CORS for React Dashboard
  svr.set_post_routing_handler([](const auto &req, auto &res) {
    res.set_header("Access-Control-Allow-Origin", "*");
    res.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS");
    res.set_header("Access-Control-Allow-Headers", "Content-Type");
  });

  svr.Options(R"(.*)", [](const auto &req, auto &res) {
    res.set_header("Access-Control-Allow-Origin", "*");
    res.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS");
    res.set_header("Access-Control-Allow-Headers", "Content-Type");
    res.status = 200;
  });

  std::cout << "Server listening on port 8080..." << std::endl;
  svr.listen("0.0.0.0", 8080);

  return 0;
}
