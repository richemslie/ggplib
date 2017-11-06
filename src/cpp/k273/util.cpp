#include "util.h"

using namespace K273;

///////////////////////////////////////////////////////////////////////////////

WorkerThread::WorkerThread(WorkerInterface* worker) :
    worker(worker),
    running(true),
    poll(false),
    waiting(false),
    worker_ready(false) {
    worker->setThread(this);
}

WorkerThread::~WorkerThread() {
}

///////////////////////////////////////////////////////////////////////////////

void WorkerThread::spawn() {
    std::thread* t = new std::thread(&WorkerThread::mainLoop, this);
    this->the_thread = std::unique_ptr<std::thread>(t);
}

void WorkerThread::startPolling() {
    this->worker_ready.store(false, std::memory_order_relaxed);
    this->waiting.store(true, std::memory_order_release);
    this->poll.store(true, std::memory_order_release);
    this->cv.notify_one();

    while (this->waiting.load(std::memory_order_acquire)) {
        ;
    }
}

void WorkerThread::stopPolling() {
    this->worker_ready.store(false, std::memory_order_relaxed);
    this->waiting.store(false, std::memory_order_release);
    this->poll.store(false, std::memory_order_release);

    while (!this->waiting.load(std::memory_order_acquire)) {
        ;
    }
}

void WorkerThread::kill() {
    this->running = false;
    this->worker_ready.store(false, std::memory_order_relaxed);
    this->poll.store(false, std::memory_order_release);

    this->cv.notify_one();
    this->the_thread->join();
}

void WorkerThread::promptWorker() {
    this->worker_ready.store(true, std::memory_order_release);
}

void WorkerThread::mainLoop() {
    while (this->running) {
        {
            std::unique_lock <std::mutex> lk(this->m);
            this->waiting.exchange(true, std::memory_order_acq_rel);
            cv.wait(lk, [this] { return this->poll || !this->running; });
        }

        this->waiting.exchange(false, std::memory_order_acq_rel);

        while (true) {
            if (!this->poll.load(std::memory_order_acquire)) {
                break;
            }

            if (this->worker_ready.load(std::memory_order_acquire)) {
                // do work must call this->done() before exiting
                this->worker->doWork();

            } else {
                // pause
                cpuRelax();
            }
        }
    }
}
