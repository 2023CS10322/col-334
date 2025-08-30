// server.cpp
// Simple TCP server for word-count assignment.
// Reads words.txt (comma-separated words) and responds to "p,k\n" requests.
//
// Behavior:
// - If p >= total_words: respond "EOF\n"
// - Otherwise return up to k words starting at offset p separated by commas.
//   If the file ends before k words are served, append "EOF" (e.g. "w1,w2,EOF\n")
// - Keeps running, handling one connection at a time (until killed with Ctrl-C).

#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <unistd.h>

#include <chrono>
#include <cstring>
#include <fstream>
#include <iostream>
#include <regex>t
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
    // fallback keys sometimes named num_iterations or num_repetitions
    cfg.num_iterations = extract_int("num_iterations");
    if (cfg.num_iterations == 0) cfg.num_iterations = extract_int("num_repetitions");
    return cfg;
}

vector<string> load_words(const string &filename) {
    ifstream in(filename);
    if (!in) {
        cerr << "Failed to open words file: " << filename << endl;
        exit(1);
    }
    string line;
    // reading whole file as single line containing comma-separated words
    string content;
    while (getline(in, line)) {
        if (!content.empty()) content += "\n";
        content += line;
    }
    vector<string> words;
    string token;
    stringstream ss(content);
    while (getline(ss, token, ',')) {
        // trim whitespace
        size_t start = token.find_first_not_of(" \t\r\n");
        size_t end = token.find_last_not_of(" \t\r\n");
        if (start == string::npos) token = "";
        else token = token.substr(start, end - start + 1);
        if (!token.empty()) words.push_back(token);
    }
    return words;
}

ssize_t recv_until_newline(int sock, string &out) {
    out.clear();
    char buf[1024];
    while (true) {
        ssize_t n = recv(sock, buf, sizeof(buf), 0);
        if (n <= 0) return n; // error or closed
        out.append(buf, buf + n);
        // stop once we have a newline
        auto pos = out.find('\n');
        if (pos != string::npos) {
            // trim after newline, keep remainder for simplicity (we don't handle pipelined requests)
            out = out.substr(0, pos + 1);
            return out.size();
        }
    }
}

int main(int argc, char **argv) {
    string cfgpath = "config.json";
    if (argc > 1) cfgpath = argv[1];

    Config cfg = parse_config(cfgpath);
    if (cfg.server_ip.empty() || cfg.server_port == 0 || cfg.filename.empty()) {
        cerr << "Invalid or incomplete config.json. Please check server_ip, server_port, filename." << endl;
        return 1;
    }

    vector<string> words = load_words(cfg.filename);
    size_t total = words.size();
    cout << "Loaded " << total << " words from '" << cfg.filename << "'\n";
    cout << "Server listening on " << cfg.server_ip << ":" << cfg.server_port << endl;

    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) {
        perror("socket");
        return 1;
    }

    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    sockaddr_in addr;
    addr.sin_family = AF_INET;
    addr.sin_port = htons(cfg.server_port);
    if (inet_pton(AF_INET, cfg.server_ip.c_str(), &addr.sin_addr) != 1) {
        cerr << "Invalid server IP: " << cfg.server_ip << endl;
        close(server_fd);
        return 1;
    }

    if (::bind(server_fd, (sockaddr*)&addr, sizeof(addr)) < 0) {
        perror("bind");
        close(server_fd);
        return 1;
    }

    if (listen(server_fd, 10) < 0) {
        perror("listen");
        close(server_fd);
        return 1;
    }

    while (true) {
        sockaddr_in cli_addr;
        socklen_t cli_len = sizeof(cli_addr);
        int client_fd = accept(server_fd, (sockaddr*)&cli_addr, &cli_len);
        if (client_fd < 0) {
            perror("accept");
            continue;
        }
        char cli_ip[INET_ADDRSTRLEN];
        inet_ntop(AF_INET, &cli_addr.sin_addr, cli_ip, INET_ADDRSTRLEN);
        cout << "Accepted connection from " << cli_ip << ":" << ntohs(cli_addr.sin_port) << endl;

        string req;
        ssize_t rr = recv_until_newline(client_fd, req);
        if (rr <= 0) {
            cerr << "Failed to receive request or connection closed\n";
            close(client_fd);
            continue;
        }
        // request expected format: p,k\n
        // trim
        req.erase(remove(req.begin(), req.end(), '\r'), req.end());
        req.erase(remove(req.begin(), req.end(), '\n'), req.end());
        int p = 0, k = 0;
        {
            // parse p,k
            stringstream s(req);
            string a, b;
            if (getline(s, a, ',') && getline(s, b)) {
                try {
                    p = stoi(a);
                    k = stoi(b);
                } catch (...) {
                    p = -1; k = 0;
                }
            } else {
                p = -1; k = 0;
            }
        }
        cout << "Request: p=" << p << " k=" << k << endl;

        string response;
        if (p < 0 || k <= 0) {
            // invalid request -> respond EOF\n (spec says handle invalid offsets)
            response = "EOF\n";
        } else if ((size_t)p >= total) {
            response = "EOF\n";
        } else {
            bool ended = false;
            for (int i = 0; i < k; ++i) {
                size_t idx = (size_t)p + (size_t)i;
                if (idx < total) {
                    response += words[idx];
                    // add comma if not last
                    response += ",";
                } else {
                    response += "EOF";
                    ended = true;
                    break;
                }
            }
            // Remove trailing comma if present and EOF not appended
            if (!response.empty() && response.back() == ',') {
                response.pop_back();
            }
            response += "\n";
            if (ended) {
                // If ended was true we already added EOF before \n (per spec example)
            }
        }

        // send response
        ssize_t snt = send(client_fd, response.c_str(), response.size(), 0);
        if (snt < 0) {
            perror("send");
        } else {
            cout << "Sent response (" << snt << " bytes): '" << response.substr(0, response.size()-1) << "'\n";
        }
        close(client_fd);
    }

    close(server_fd);
    return 0;
}
