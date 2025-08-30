// client.cpp
// Simple TCP client for word-count assignment.
// Reads config.json, connects to server_ip:server_port, sends "p,k\n",
// receives response (terminated by newline), counts word frequencies and prints them.

#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <unistd.h>

#include <algorithm>
#include <cstring>
#include <fstream>
#include <iostream>
#include <map>
#include <regex>
#include <sstream>
#include <string>
#include <vector>

using namespace std;

struct Config {
    string server_ip;
    int server_port;
    int k;
    int p;
    string filename;
    int num_iterations;
};

Config parse_config(const string &path) {
    Config cfg;
    ifstream in(path);
    if (!in) {
        cerr << "Failed to open config file: " << path << endl;
        exit(1);
    }
    string s((istreambuf_iterator<char>(in)), istreambuf_iterator<char>());
    auto extract_str = [&](const string &key)->string {
        regex r("\"" + key + "\"\\s*:\\s*\"([^\"]+)\"");
        smatch m;
        if (regex_search(s, m, r)) return m[1];
        return string();
    };
    auto extract_int = [&](const string &key)->int {
        regex r("\"" + key + "\"\\s*:\\s*([0-9]+)");
        smatch m;
        if (regex_search(s, m, r)) return stoi(m[1]);
        return 0;
    };
    cfg.server_ip = extract_str("server_ip");
    cfg.server_port = extract_int("server_port");
    cfg.k = extract_int("k");
    cfg.p = extract_int("p");
    cfg.filename = extract_str("filename");
    cfg.num_iterations = extract_int("num_iterations");
    if (cfg.num_iterations == 0) cfg.num_iterations = extract_int("num_repetitions");
    return cfg;
}

ssize_t recv_until_newline(int sock, string &out) {
    out.clear();
    char buf[1024];
    while (true) {
        ssize_t n = recv(sock, buf, sizeof(buf), 0);
        if (n <= 0) return n;
        out.append(buf, buf + n);
        auto pos = out.find('\n');
        if (pos != string::npos) {
            out = out.substr(0, pos + 1);
            return out.size();
        }
    }
}

int main(int argc, char **argv) {
    string cfgpath = "config.json";
    if (argc > 1) cfgpath = argv[1];

    Config cfg = parse_config(cfgpath);
    if (cfg.server_ip.empty() || cfg.server_port == 0) {
        cerr << "Invalid config.json (missing server_ip or server_port)\n";
        return 1;
    }

    // Build request p,k\n
    stringstream reqss;
    reqss << cfg.p << "," << cfg.k << "\n";
    string request = reqss.str();

    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) {
        perror("socket");
        return 1;
    }

    sockaddr_in serv_addr;
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(cfg.server_port);
    if (inet_pton(AF_INET, cfg.server_ip.c_str(), &serv_addr.sin_addr) != 1) {
        cerr << "Invalid server IP: " << cfg.server_ip << endl;
        close(sock);
        return 1;
    }

    if (connect(sock, (sockaddr*)&serv_addr, sizeof(serv_addr)) < 0) {
        perror("connect");
        close(sock);
        return 1;
    }

    // send request
    ssize_t sent = send(sock, request.c_str(), request.size(), 0);
    if (sent < 0) {
        perror("send");
        close(sock);
        return 1;
    }

    // receive response until newline
    string resp;
    ssize_t r = recv_until_newline(sock, resp);
    if (r <= 0) {
        cerr << "No response or connection closed\n";
        close(sock);
        return 1;
    }
    // strip newline and CR
    resp.erase(remove(resp.begin(), resp.end(), '\r'), resp.end());
    if (!resp.empty() && resp.back() == '\n') resp.pop_back();

    // parse response: comma-separated tokens
    vector<string> tokens;
    string token;
    stringstream ss(resp);
    while (getline(ss, token, ',')) {
        // trim
        size_t start = token.find_first_not_of(" \t\r\n");
        size_t end = token.find_last_not_of(" \t\r\n");
        string t;
        if (start == string::npos) t = "";
        else t = token.substr(start, end - start + 1);
        if (!t.empty()) tokens.push_back(t);
    }

    map<string, int> freq;
    for (auto &t : tokens) {
        if (t == "EOF") continue;
        freq[t] += 1;
    }

    // print frequencies, one per line "word, count"
    for (auto &kv : freq) {
        cout << kv.first << ", " << kv.second << "\n";
    }

    close(sock);
    return 0;
}
