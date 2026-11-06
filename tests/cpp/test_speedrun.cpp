// Host-side unit tests for the speedrun core (no Half-Life engine required).
#include "sr_core.h"

#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>

static int checks = 0;
static int failures = 0;

#define CHECK(expr)                                                            \
    do {                                                                       \
        ++checks;                                                              \
        if (!(expr)) {                                                         \
            std::cerr << "FAIL line " << __LINE__ << ": " << #expr << '\n';    \
            ++failures;                                                        \
        }                                                                      \
    } while (0)

#define CHECK_THROWS(expr, exc_type)                                           \
    do {                                                                       \
        ++checks;                                                              \
        bool threw = false;                                                    \
        try {                                                                  \
            (void)(expr);                                                      \
        } catch (const exc_type&) {                                            \
            threw = true;                                                      \
        } catch (...) {                                                        \
        }                                                                      \
        if (!threw) {                                                          \
            std::cerr << "FAIL line " << __LINE__ << ": expected "             \
                      << #exc_type << " from " << #expr << '\n';               \
            ++failures;                                                        \
        }                                                                      \
    } while (0)

static void test_route() {
    CHECK(sr::Route::ChapterCount() == 13);
    CHECK(sr::Route::Maps().size() == 39);
    CHECK(sr::Route::Maps(true).size() == 44);
    CHECK(sr::Route::Maps().front() == "of0a0");
    CHECK(sr::Route::LastMap() == "of7a0");
    CHECK(sr::Route::BootCampMapCount() == 5);
    CHECK(sr::Route::IsKnownMap("of1a4b"));
    CHECK(!sr::Route::IsKnownMap("ofboot0"));
    CHECK(!sr::Route::IsKnownMap("c1a0"));
    CHECK(sr::Route::MapIndex("of1a4b") == 5);
    CHECK(sr::Route::ChapterIndexFor("of1a4b") == 1);
    CHECK(sr::Route::ChapterIndexFor("of7a0") == 12);
    CHECK(sr::Route::ChapterIndexFor("nope") == -1);
    CHECK(std::string(sr::Route::Chapters()[8].name_en) == "Pit Worm's Nest");
}

static void test_format_time() {
    CHECK(sr::FormatTime(0) == "0:00.000");
    CHECK(sr::FormatTime(62345) == "1:02.345");
    CHECK(sr::FormatTime(-50) == "0:00.000");
    CHECK(sr::FormatTime(3661001) == "1:01:01.001");
    CHECK(sr::FormatTime(59999) == "0:59.999");
}

static void test_timer_lifecycle() {
    sr::FakeClock clock;
    sr::RunTimer timer(clock);
    CHECK(timer.ElapsedMs() == 0);
    CHECK(!timer.IsRunning());
    CHECK_THROWS(timer.Pause(), std::logic_error);
    CHECK_THROWS(timer.Resume(), std::logic_error);
    CHECK_THROWS(timer.SplitAt("of0a0"), std::logic_error);

    clock.Advance(1000);
    timer.Start();
    CHECK(timer.IsRunning());
    CHECK_THROWS(timer.Start(), std::logic_error);
    clock.Advance(1000);
    CHECK(timer.ElapsedMs() == 1000);

    timer.Pause();
    CHECK(timer.IsPaused());
    clock.Advance(5000);  // paused time must not count
    CHECK(timer.ElapsedMs() == 1000);
    CHECK_THROWS(timer.SplitAt("of0a0"), std::logic_error);
    timer.Resume();
    clock.Advance(500);
    CHECK(timer.ElapsedMs() == 1500);

    CHECK(timer.SplitAt("of0a0") == 1500);
    CHECK(timer.Splits().size() == 1);
    CHECK(timer.Splits()[0].map == "of0a0");
    CHECK(!timer.Splits()[0].has_pb);
    CHECK_THROWS(timer.SplitAt("of0a0"), std::logic_error);
    CHECK_THROWS(timer.SplitAt("c1a0"), std::invalid_argument);

    timer.Finish();
    CHECK(timer.IsFinished());
    CHECK(timer.ElapsedMs() == 1500);
    clock.Advance(10000);
    CHECK(timer.ElapsedMs() == 1500);  // frozen at finish
    CHECK_THROWS(timer.SplitAt("of1a1"), std::logic_error);

    timer.Reset();
    CHECK(timer.Splits().empty());
    CHECK(timer.ElapsedMs() == 0);
    CHECK(!timer.IsFinished());
}

static void test_pb_and_splits() {
    sr::FakeClock clock;
    std::map<std::string, sr::Ms> pb = {{"of0a0", 2000}, {"of1a1", 10000}};
    sr::RunTimer timer(clock, pb);
    timer.Start();
    clock.Advance(1500);
    timer.SplitAt("of0a0");
    clock.Advance(1000);
    timer.SplitAt("of1a1");
    CHECK(timer.Splits().size() == 2);
    CHECK(timer.Splits()[0].has_pb);
    CHECK(timer.Splits()[0].delta == -500);
    CHECK(timer.Splits()[1].delta == -7500);
    CHECK(timer.Splits()[1].route_index == 1);

    const std::string csv = sr::RenderSplitsCsv(timer);
    CHECK(csv.find("map,at_ms,delta_ms,has_pb,route_index") == 0);
    CHECK(csv.find("of0a0,1500,-500,1,0") != std::string::npos);

    const std::string serialized = timer.SerializePB();
    CHECK(serialized.find("of0a0=1500") != std::string::npos);
    std::istringstream in(serialized + "garbage\n=5\nof1a1=-99\n# comment\nof7a0=abc\n");
    const auto parsed = sr::ParsePersonalBest(in);
    CHECK(parsed.size() == 2);
    CHECK(parsed.at("of0a0") == 1500);
    CHECK(parsed.at("of1a1") == 2500);
}

static void test_auto_finish_and_config() {
    sr::FakeClock clock;
    sr::RunTimer timer(clock);
    timer.Start();
    clock.Advance(1234);
    timer.SplitAt("of7a0");
    CHECK(timer.IsFinished());
    CHECK(timer.ElapsedMs() == 1234);

    sr::ConfigOptions opts;
    opts.hud = false;
    opts.practice = true;
    opts.hud_x = 10;
    const std::string cfg = sr::RenderConfig(opts);
    CHECK(cfg.find("sr_timer_hud \"0\"") != std::string::npos);
    CHECK(cfg.find("sr_practice_mode \"1\"") != std::string::npos);
    CHECK(cfg.find("sr_timer_hud_pos \"10 4\"") != std::string::npos);
    CHECK(cfg.find("sv_cheats \"0\"") != std::string::npos);
    CHECK(cfg.find("sv_cheats \"1\"") == std::string::npos);

    sr::SystemClock real;
    CHECK(real.NowMs() > 0);
}

int main() {
    test_route();
    test_format_time();
    test_timer_lifecycle();
    test_pb_and_splits();
    test_auto_finish_and_config();
    std::cout << "speedrun core: " << checks << " checks, " << failures << " failure(s)\n";
    return failures == 0 ? 0 : 1;
}
