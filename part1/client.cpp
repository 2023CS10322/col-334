#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>
#include <fstream>
#include <iostream>
#include <map>
#include <sstream>
#include <string>
#include <vector>
#include <algorithm>
#include <chrono>

using namespace std;

// Same config parser as in server
map<string, string> load_config(const string &filename) {
    ifstream file(filename);
    map<string, string> config;
    string line;
    while (getline(file, line)) {
        line.erase(remove(line.begin(), line.end(), ' '), line.end());
        if (line.empty() || line[0] == '{' || line[0] == '}') continue;

        size_t key_start = line.find('"');
        size_t key_end = line.find('"', key_start + 1);
        string key = line.substr(key_start + 1, key_end - key_start - 1);

        size_t colon = line.find(':', key_end);
        string value = line.substr(colon + 1);

        value.erase(remove(value.begin(), value.end(), '"'), value.end());
        value.erase(remove(value.begin(), value.end(), ','), value.end());
        value.erase(remove(value.begin(), value.end(), '\n'), value.end());

        config[key] = value;
    }
    return config;
}

int main() {
    using namespace std::chrono;
    auto start = high_resolution_clock::now();
    
    auto config = load_config("config.json");

    string server_ip = config["server_ip"];
    int server_port = stoi(config["server_port"]);
    int k = stoi(config["k"]);
    int p = stoi(config["p"]);

    int sockfd = socket(AF_INET, SOCK_STREAM, 0);
    sockaddr_in serv_addr{};
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = inet_addr(server_ip.c_str());
    serv_addr.sin_port = htons(server_port);

    connect(sockfd, (sockaddr*)&serv_addr, sizeof(serv_addr));

    map<string, int> freq;
    while (true) {
        string request = to_string(p) + "," + to_string(k) + "\n";
        send(sockfd, request.c_str(), request.size(), 0);

        char buffer[1024];
        int n = read(sockfd, buffer, sizeof(buffer) - 1);
        if (n <= 0) break;
        buffer[n] = '\0';

        string resp(buffer);
        stringstream ss(resp);
        string word;
        while (getline(ss, word, ',')) {
            if (word == "EOF\n" || word == "EOF") {
                goto DONE;
            }
            freq[word]++;
        }
        p += k;
    }

DONE:
    close(sockfd);
    auto end = high_resolution_clock::now();
    auto elapsed = duration_cast<milliseconds>(end - start).count();

    for (auto &it : freq) {
        cout << it.first << ", " << it.second << endl;
    }
    cout << "ELAPSED_MS:" << elapsed << endl;
    return 0;
}
