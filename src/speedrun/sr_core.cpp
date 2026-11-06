// BugfixedHL x Opposing Force - Speedrun Merge Kit
// See sr_core.h. Deliberately free of Half-Life engine dependencies.
#include "sr_core.h"

#include <algorithm>
#include <chrono>
#include <cstdio>
#include <sstream>
#include <stdexcept>
#include <utility>

#include "sr_route_data.h"

namespace sr {

Ms SystemClock::NowMs() const {
    const auto now = std::chrono::steady_clock::now().time_since_epoch();
    return std::chrono::duration_cast<std::chrono::milliseconds>(now).count();
}

std::string FormatTime(Ms ms) {
    if (ms < 0) {
        ms = 0;
    }
    const long long total = static_cast<long long>(ms);
    const long long hours = total / 3600000;
    const long long minutes = (total / 60000) % 60;
    const long long seconds = (total / 1000) % 60;
    const long long millis = total % 1000;
    char buffer[64];
    if (hours > 0) {
        std::snprintf(buffer, sizeof(buffer), "%lld:%02lld:%02lld.%03lld",
                      hours, minutes, seconds, millis);
    } else {
        std::snprintf(buffer, sizeof(buffer), "%lld:%02lld.%03lld",
                      minutes, seconds, millis);
    }
    return std::string(buffer);
}

const ChapterData* Route::Chapters() { return route_data::kChapters; }
int Route::ChapterCount() { return route_data::kChapterCount; }

std::vector<std::string> Route::Maps(bool include_boot_camp) {
    std::vector<std::string> maps;
    for (int c = 0; c < ChapterCount(); ++c) {
        const ChapterData& ch = Chapters()[c];
        for (int i = 0; i < ch.map_count; ++i) {
            maps.emplace_back(ch.maps[i]);
        }
    }
    if (include_boot_camp) {
        for (int i = 0; i < BootCampMapCount(); ++i) {
            maps.emplace_back(BootCampMaps()[i]);
        }
    }
    return maps;
}

int Route::MapIndex(const std::string& map) {
    const std::vector<std::string> maps = Maps();
    const auto it = std::find(maps.begin(), maps.end(), map);
    return it == maps.end() ? -1 : static_cast<int>(it - maps.begin());
}

bool Route::IsKnownMap(const std::string& map) { return MapIndex(map) >= 0; }

int Route::ChapterIndexFor(const std::string& map) {
    const int index = MapIndex(map);
    if (index < 0) {
        return -1;
    }
    int seen = 0;
    for (int c = 0; c < ChapterCount(); ++c) {
        seen += Chapters()[c].map_count;
        if (index < seen) {
            return c;
        }
    }
    return -1;
}

const char* const* Route::BootCampMaps() { return route_data::kBootCampMaps; }
int Route::BootCampMapCount() { return route_data::kBootCampMapCount; }
std::string Route::LastMap() {
    const std::vector<std::string> maps = Maps();
    return maps.empty() ? std::string() : maps.back();
}

RunTimer::RunTimer(IClock& clock, std::map<std::string, Ms> personal_best)
    : clock_(clock), pb_(std::move(personal_best)) {}

void RunTimer::Reset() {
    state_ = State::Idle;
    splits_.clear();
    start_ms_ = 0;
    paused_at_ = 0;
    paused_total_ = 0;
    last_index_ = -1;
    finish_ms_ = 0;
}

void RunTimer::Start() {
    if (state_ == State::Running || state_ == State::Paused) {
        throw std::logic_error("sr::RunTimer: Start() called while a run is active");
    }
    Reset();
    start_ms_ = clock_.NowMs();
    state_ = State::Running;
}

void RunTimer::Pause() {
    if (state_ != State::Running) {
        throw std::logic_error("sr::RunTimer: Pause() requires a running timer");
    }
    paused_at_ = clock_.NowMs();
    state_ = State::Paused;
}

void RunTimer::Resume() {
    if (state_ != State::Paused) {
        throw std::logic_error("sr::RunTimer: Resume() requires a paused timer");
    }
    paused_total_ += clock_.NowMs() - paused_at_;
    state_ = State::Running;
}

void RunTimer::Finish() {
    if (state_ == State::Idle) {
        throw std::logic_error("sr::RunTimer: Finish() requires a started timer");
    }
    finish_ms_ = ElapsedMs();
    state_ = State::Finished;
}

Ms RunTimer::ElapsedMs() const {
    switch (state_) {
        case State::Idle:
            return 0;
        case State::Paused:
            return paused_at_ - start_ms_ - paused_total_;
        case State::Finished:
            return finish_ms_;
        case State::Running:
            break;
    }
    return clock_.NowMs() - start_ms_ - paused_total_;
}

Ms RunTimer::SplitAt(const std::string& map) {
    if (state_ != State::Running) {
        throw std::logic_error("sr::RunTimer: SplitAt() requires a running timer");
    }
    const int index = Route::MapIndex(map);
    if (index < 0) {
        throw std::invalid_argument("sr::RunTimer: unknown OP4 map: " + map);
    }
    if (index <= last_index_) {
        throw std::logic_error("sr::RunTimer: splits must follow the route order: " + map);
    }
    const Ms at = ElapsedMs();
    Split split;
    split.map = map;
    split.at = at;
    split.route_index = index;
    const auto pb = pb_.find(map);
    if (pb != pb_.end()) {
        split.has_pb = true;
        split.delta = at - pb->second;
    }
    splits_.push_back(split);
    last_index_ = index;
    if (map == Route::LastMap()) {
        finish_ms_ = at;
        state_ = State::Finished;
    }
    return at;
}

std::string RunTimer::SerializePB() const {
    std::ostringstream out;
    out << "# BHLxOP4 personal best - map=ms\n";
    for (const Split& split : splits_) {
        out << split.map << '=' << split.at << '\n';
    }
    return out.str();
}

std::map<std::string, Ms> ParsePersonalBest(std::istream& in) {
    std::map<std::string, Ms> pb;
    std::string line;
    while (std::getline(in, line)) {
        if (line.empty() || line[0] == '#' || line[0] == '/' || line[0] == ' ') {
            continue;
        }
        const std::size_t eq = line.find('=');
        if (eq == std::string::npos || eq == 0) {
            continue;
        }
        try {
            std::size_t used = 0;
            const Ms value = std::stoll(line.substr(eq + 1), &used);
            if (used > 0 && value >= 0) {
                pb[line.substr(0, eq)] = value;
            }
        } catch (const std::exception&) {
            // A corrupt PB line must never break a run.
        }
    }
    return pb;
}

std::string RenderConfig(const ConfigOptions& o) {
    std::ostringstream out;
    out << "// generated by sr::RenderConfig - sv_cheats stays 0\n"
        << "sr_timer_enable \"" << (o.timer ? 1 : 0) << "\"\n"
        << "sr_timer_hud \"" << (o.hud ? 1 : 0) << "\"\n"
        << "sr_timer_hud_pos \"" << o.hud_x << " " << o.hud_y << "\"\n"
        << "sr_autodemo \"" << (o.autodemo ? 1 : 0) << "\"\n"
        << "sr_splits_announce \"" << (o.splits_announce ? 1 : 0) << "\"\n"
        << "sr_practice_mode \"" << (o.practice ? 1 : 0) << "\"\n"
        << "sr_pb_path \"" << o.pb_path << "\"\n"
        << "sv_cheats \"0\"\n";
    return out.str();
}

std::string RenderSplitsCsv(const RunTimer& timer) {
    std::ostringstream out;
    out << "map,at_ms,delta_ms,has_pb,route_index\n";
    for (const Split& s : timer.Splits()) {
        out << s.map << ',' << s.at << ',' << s.delta << ','
            << (s.has_pb ? 1 : 0) << ',' << s.route_index << '\n';
    }
    return out.str();
}

}  // namespace sr
