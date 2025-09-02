#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>
#include <fstream>
#include <iostream>
#include <sstream>
#include <vector>
#include <string>
#include <jsoncpp/json/json.h>

using namespace std;

vector<string> words;

void load_words(const string &filename) {
    ifstream file(filename);
    string line;
    if (file) {
        getline(file, line);
        stringstream ss(line);
        string word;
        while (getline(ss, word, ',')) {
            words.push_back(word);
        }
    }
}

string handle_request(int p, int k) {
    if (p >= (int)words.size()) {
        return "EOF\n";
    }
    stringstream ss;
    int count = 0;
    for (int i = p; i < (int)words.size() && count < k; i++, count++) {
        ss << words[i];
        if (count < k - 1 && i < (int)words.size() - 1) ss << ",";
    }
    if (p + k >= (int)words.size()) {
        ss << (count > 0 ? "," : "") << "EOF";
    }
    ss << "\n";
    return ss.str();
}

int main() {
    // Read config.json
    ifstream cfg("config.json");
    Json::Value config;
    cfg >> config;
    string server_ip = config["server_ip"].asString();
    int server_port = config["server_port"].asInt();
    string filename = config["filename"].asString();

    load_words(filename);

    int sockfd = socket(AF_INET, SOCK_STREAM, 0);
    sockaddr_in serv_addr{};
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = inet_addr(server_ip.c_str());
    serv_addr.sin_port = htons(server_port);

    bind(sockfd, (sockaddr*)&serv_addr, sizeof(serv_addr));
    listen(sockfd, 5);

    cout << "Server listening on " << server_ip << ":" << server_port << endl;

    while (true) {
        int client_fd = accept(sockfd, nullptr, nullptr);
        char buffer[1024];
        while (true) {
            int n = read(client_fd, buffer, sizeof(buffer) - 1);
            if (n <= 0) break;
            buffer[n] = '\0';

            string req(buffer);
            int p, k;
            char comma;
            stringstream ss(req);
            ss >> p >> comma >> k;

            string response = handle_request(p, k);
            send(client_fd, response.c_str(), response.size(), 0);

            if (response.find("EOF") != string::npos) break;
        }
        close(client_fd);
    }

    close(sockfd);
    return 0;
}
