export default function Home() {
  return (
    <>
      {/* HERO SECTION */}
      <section className="relative bg-black text-white py-32 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-black to-zinc-900 opacity-80"></div>

        <div className="relative max-w-6xl mx-auto px-6 text-center">
          <h1 className="text-5xl md:text-7xl font-extrabold leading-tight">
            YOUR TEAM CLOSES DEALS.
          </h1>
          <p className="mt-6 text-xl md:text-2xl text-gray-300">
            IntentBrain handles everything before that.
          </p>

          <button className="mt-10 px-10 py-4 bg-green-500 hover:bg-green-600 text-black font-bold rounded-xl text-lg shadow-xl">
            Hear The AI Live
          </button>
        </div>
      </section>

      {/* VIDEO SECTION */}
      <section className="py-20 bg-gradient-to-b from-white to-slate-100 dark:from-zinc-900 dark:to-zinc-900">
        <div className="max-w-4xl mx-auto shadow-2xl rounded-xl overflow-hidden">
          <iframe
            width="100%"
            height="500"
            src="https://www.youtube.com/embed/cVcHj5UHqm0"
            title="YouTube video player"
            frameBorder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
            allowFullScreen
          ></iframe>
        </div>
      </section>

      {/* STATS SECTION */}
      <section className="py-20 max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-10 text-center">
        <div>
          <h2 className="text-5xl font-bold text-green-500">92%</h2>
          <p className="text-gray-400 mt-2">High Intent Conversations</p>
        </div>
        <div>
          <h2 className="text-5xl font-bold text-green-500">243</h2>
          <p className="text-gray-400 mt-2">Meetings Booked</p>
        </div>
        <div>
          <h2 className="text-5xl font-bold text-green-500">56</h2>
          <p className="text-gray-400 mt-2">Live Transfers</p>
        </div>
      </section>
    </>
  );
}
