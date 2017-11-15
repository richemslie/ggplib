#pragma once

#include <mutex>
#include <queue>
#include <atomic>
#include <thread>
#include <vector>
#include <condition_variable>

#include "util.h"

#define likely(x)    __builtin_expect(!!(x), 1)
#define unlikely(x)  __builtin_expect(!!(x), 0)
#define PACKED __attribute__((__packed__))

namespace K273 {

    inline void cpuRelax() {
        __asm__ __volatile__("rep; nop" : : : "memory");
    }

    // read time stamp counter
    inline uint64_t rdtsc() {
        uint32_t hi_ticks, lo_ticks;
        __asm__ __volatile__ ("rdtsc" : "=a" (lo_ticks), "=d" (hi_ticks));
        return (static_cast<uint64_t> (hi_ticks) << 32) | lo_ticks;
    }

    inline double get_rtc_relative_time() {
        /* use this judiciously, for high performance relative time based stuff */
        return rdtsc() / 30000.0;
    }

    inline double get_time() {
        timespec ts;
        if (likely(clock_gettime(CLOCK_REALTIME, &ts) == 0)) {
            return ts.tv_sec + ((double) ts.tv_nsec) / 1000000000.0;
        }

        return -1;
    }

    class Random {
    public:
        Random(unsigned int seed = 0) :
            seed(seed) {

            if (this->seed == 0) {
                timespec ts;
                for (int ii=0; ii<5; ii++) {
                    clock_gettime(CLOCK_REALTIME, &ts);
                    this->seed += ts.tv_nsec;
                }
            }
        }

        unsigned short getShort() {
            this->seed = (214013 * this->seed + 2531011);
            return (this->seed >> 16 & 0x7FFF);
        }

        unsigned short getWithMax(unsigned short max_num) {
            if (unlikely(max_num == 0)) {
                return 0;
            }

            return this->getShort() % max_num;
        }

    private:
        unsigned int seed;
    };

    // this is a thread safe queue...  it is used to communicate back from worker threads, to
    // caller threads safely.  It was this crudest implementation to get things up and running.
    // However, it seems very, very fast...  So no point optimizing for the sake of it, right now.

    class SpinLock {
    public:
        SpinLock() :
            locked(false) {
        }

        void lock() {
            while (this->locked.exchange(true, std::memory_order_acq_rel)) {
                cpuRelax();
            }
        }

        void unlock() {
            this->locked.store(false, std::memory_order_release);
        }

    private:
        std::atomic <bool> locked;
        char padding_buf[64 - sizeof(std::atomic<bool>)];
    };

    class SpinLockGuard {
    public:
        SpinLockGuard(SpinLock& l):
            spin_lock(l) {
            this->spin_lock.lock();
        }

        ~SpinLockGuard() {
            this->spin_lock.unlock();
        }

    private:
        SpinLock& spin_lock;
    };

    class WorkerThread;

    template <typename T>
    class LockedQueue {
    public:
        void push(T new_value) {
            std::lock_guard <std::mutex> lk(this->mut);
            // SpinLockGuard g(this->spin_lock);
            this->data_queue.push(new_value);
        }

        T pop() {
            std::lock_guard <std::mutex> lk(this->mut);
            // SpinLockGuard g(this->spin_lock);
            if (this->data_queue.empty()) {
                return nullptr;
            }

            T res = this->data_queue.front();
            this->data_queue.pop();
            return res;
        }

        bool empty() {
            std::lock_guard <std::mutex> lk(this->mut);
            // SpinLockGuard g(this->spin_lock);
            return this->data_queue.empty();
        }

    private:
        std::mutex mut;
        //SpinLock spin_lock;
        std::queue <T> data_queue;
    };

    ///////////////////////////////////////////////////////////////////////////////

    class WorkerInterface {
    public:
        WorkerInterface() :
            thread_self(nullptr) {
        }

        virtual ~WorkerInterface() {
        }

    public:
        WorkerThread* getThread() {
            return this->thread_self;
        }

        void setThread(WorkerThread* t) {
            this->thread_self = t;
        }

    public:
        // The interface
        virtual void doWork() = 0;

    protected:
        WorkerThread* thread_self;
    };

    class WorkerThread {
    public:
        WorkerThread(WorkerInterface* worker);
        ~WorkerThread();

    public:
        // interface from main thread:
        void spawn();
        void startPolling();
        void stopPolling();
        void kill();

        void promptWorker();

        // yes this is non const, since only time should get reference when it is not doing work.
        // Up to the callee to call this is the right time (or things will implode).
        WorkerInterface* getWorker() {
            return this->worker;
        }

        // interface from worker thread
        void done() {
            this->worker_ready.exchange(false, std::memory_order_acq_rel);
        }

    private:
        void mainLoop();

    private:
        WorkerInterface* worker;

        std::mutex m;
        std::condition_variable cv;
        bool running;

        std::atomic <bool> poll;
        std::atomic <bool> waiting;
        std::atomic <bool> worker_ready;

        std::unique_ptr<std::thread> the_thread;
    };

    // Simple non-copyable base (XXX why do this - just use = delete, seems cleaner).
    class NonCopyable {
    protected:
        NonCopyable() {
        }

        ~NonCopyable() {
        }

    private:
        NonCopyable(const NonCopyable &) = delete;
        NonCopyable& operator= (const NonCopyable &) = delete;
    };
}
