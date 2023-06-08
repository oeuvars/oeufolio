import React, { useState, useEffect } from "react";
import playIcon from "../assets/Icons/play.svg";
import pauseIcon from "../assets/Icons/pause.svg";
import song from "../assets/Audio/NoOneReallyCares.mp3";
import { motion } from "framer-motion";

let audio = new Audio(song);

const PlayPauseButton = () => {
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    audio.addEventListener("ended", handleAudioEnded); // Listen for the 'ended' event
    return () => {
      audio.removeEventListener("ended", handleAudioEnded); // Clean up the event listener
    };
  }, []);

  const handlePlayPause = () => {
    if (audio.paused) {
      audio.play();
      setIsPlaying(true);
    } else {
      audio.pause();
      setIsPlaying(false);
    }
  };

  const handleAudioEnded = () => {
    setIsPlaying(false);
  };

  return (
    <motion.button
      onClick={handlePlayPause}
      initial={{ opacity: 0, scale: 0 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0 }}
      className="transition duration-500 my-auto"
    >
      {!isPlaying ? (
        <img src={playIcon} alt="Play" className="w-8 h-10" />
      ) : (
        <img src={pauseIcon} alt="Pause" className="w-8 h-8" />
      )}
    </motion.button>
  );
};

export default PlayPauseButton;
