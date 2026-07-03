import React from "react"
import { Link } from "react-router-dom"

export function HomePage() {
  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-white mb-8 text-center">
        mycompress
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link
          to="/image"
          className="bg-gray-800 border border-gray-700 rounded-lg p-6 text-center hover:bg-gray-700 transition-colors"
        >
          <h2 className="text-xl font-bold text-white mb-2">Image</h2>
          <p className="text-gray-400">Compress, decompress, and hide messages</p>
        </Link>

        <Link
          to="/audio"
          className="bg-gray-800 border border-gray-700 rounded-lg p-6 text-center hover:bg-gray-700 transition-colors"
        >
          <h2 className="text-xl font-bold text-white mb-2">Audio</h2>
          <p className="text-gray-400">Compress and hide messages in WAV</p>
        </Link>

        <Link
          to="/video"
          className="bg-gray-800 border border-gray-700 rounded-lg p-6 text-center hover:bg-gray-700 transition-colors"
        >
          <h2 className="text-xl font-bold text-white mb-2">Video</h2>
          <p className="text-gray-400">Compress and hide messages in MP4</p>
        </Link>
      </div>
    </div>
  )
}