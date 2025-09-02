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
#include <jsoncpp/json/json.h>

using namespace std;

int main() {
    // Read config.json
    ifstream cfg("config.json");
    Json::Value config;
    cfg >> config;
    string server_ip = config["server_ip"].asString();
    int server_port = config["server_port"].asInt();
    int k = config["k"].asInt();
    int p = config["p"].asInt();

    // Setup TCP socket
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

    for (auto &it : freq) {
        cout << it.first << ", " << it.second << endl;
    }
    return 0;
}
