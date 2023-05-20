import React from "react";
import LineGradient from "../components/LineGradient";
import { motion } from "framer-motion";
import day1 from '../assets/1.webp';
import day2 from '../assets/14.jpg';
import day3 from '../assets/3.webp';
import day4 from '../assets/4.webp';
import day5 from '../assets/5.webp';
import day6 from '../assets/6.webp';
import day7 from "../assets/7.webp";
import day8 from "../assets/8.webp";
import day9 from "../assets/9.webp";
import day10 from "../assets/10.webp";
import day11 from "../assets/11.webp";
import day12 from "../assets/12.webp";
import day13 from "../assets/13.webp";
import day14 from "../assets/15.jpg";
import day16 from "../assets/16.jpg";
import day17 from "../assets/17.jpg";

const Projects = () => {
  return (
    <section id="designs" className="phone:pt-64 phone:mt-3 xs:pt-10 sm:pt-0 tablet:pt-0 lg:pt-72 md:pt-10">

      {/* HEADINGS */}
      <motion.div
        className="md:w-2/5 mx-auto text-center"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.5 }}
        transition={{ duration: 0.5 }}
        variants={{
          hidden: { opacity: 0, y: -50 },
          visible: { opacity: 1, y: 0 },
        }}
      >
        <div className="mt-10">
          <p className="font-playfair text-black font-semibold text-4xl">
            DESIGNS
          </p>
          <div className="flex justify-center mt-5">
            <LineGradient width="w-1/3" />
          </div>
        </div>
        <p className="pt-10 text-jet font-medium font-outfit md:pb-10 lg:pb-0">
          While very diverse, our aesthetic approach often involves distinct sense of play, aiming to put the fun in functional. Strategically, my work aims to elevate design offerings by distilling core messaging down to its clearest and freshest visual form.
        </p>
      </motion.div>

      {/* PROJECTS */}
      <motion.div className="grid md:grid-cols-4 phone:grid-cols-2 lg:gap-10 phone:gap-x-4 pt-16 phone:pb-1 lg:pb-10 lg:flex-row lg:flex-wrap">
            <motion.div className="scale-100 hover:scale-105 ease-in transition duration-300 basis-1/3 flex-1 phone:pb-2 md:pb-0 phone:pt-2 md:pt-0">
              <img src={day1} alt="" className="rounded-md mx-auto object-cover shadow-lg" width={'100%'} height={'100%'}/>
            </motion.div>
            <motion.div className="scale-100 hover:scale-105 ease-in transition duration-300 basis-1/3 flex-1 phone:pb-2 md:pb-0 phone:pt-2 md:pt-0">
              <img src={day12} alt="" className="rounded-md mx-auto object-cover shadow-lg" width={'100%'} height={'100%'}/>
            </motion.div>
            <motion.div className="scale-100 hover:scale-105 ease-in transition duration-300 basis-1/3 flex-1 phone:pb-2 md:pb-0 phone:pt-2 md:pt-0">
              <img src={day3} alt="" className="rounded-md mx-auto object-cover shadow-lg" width={'100%'} height={'100%'}/>
            </motion.div>
            <motion.div className="scale-100 hover:scale-105 ease-in transition duration-300 basis-1/3 flex-1 phone:pb-2 md:pb-0 phone:pt-2 md:pt-0">
              <img src={day13} alt="" className="rounded-md mx-auto object-cover shadow-lg" width={'100%'} height={'100%'}/>
            </motion.div>
            <motion.div className="scale-100 hover:scale-105 ease-in transition duration-300 basis-1/3 flex-1 phone:pb-2 md:pb-0 phone:pt-2 md:pt-0">
              <img src={day4} alt="" className="rounded-md mx-auto object-cover shadow-lg" width={'100%'} height={'100%'}/>
            </motion.div>
            <motion.div className="scale-100 hover:scale-105 ease-in transition duration-300 basis-1/3 flex-1 phone:pb-2 md:pb-0 phone:pt-2 md:pt-0">
              <img src={day11} alt="" className="rounded-md mx-auto object-cover shadow-lg" width={'100%'} height={'100%'}/>
            </motion.div>
            <motion.div className="scale-100 hover:scale-105 ease-in transition duration-300 basis-1/3 flex-1 phone:pb-2 md:pb-0 phone:pt-2 md:pt-0">
              <img src={day2} alt="" className="rounded-md mx-auto object-cover shadow-lg" width={'100%'} height={'100%'}/>
            </motion.div>
            <motion.div className="scale-100 hover:scale-105 ease-in transition duration-300 basis-1/3 flex-1 phone:pb-2 md:pb-0 phone:pt-2 md:pt-0">
              <img src={day5} alt="" className="rounded-md mx-auto object-cover shadow-lg" width={'100%'} height={'100%'}/>
            </motion.div>
            <motion.div className="scale-100 hover:scale-105 ease-in transition duration-300 basis-1/3 flex-1 phone:pb-2 md:pb-0 phone:pt-2 md:pt-0">
              <img src={day6} alt="" className="rounded-md mx-auto object-cover shadow-lg" width={'100%'} height={'100%'}/>
            </motion.div>
            <motion.div className="scale-100 hover:scale-105 ease-in transition duration-300 basis-1/3 flex-1 phone:pb-2 md:pb-0 phone:pt-2 md:pt-0">
              <img src={day14} alt="" className="rounded-md mx-auto object-cover shadow-lg" width={'100%'} height={'100%'}/>
            </motion.div>
            <motion.div className="scale-100 hover:scale-105 ease-in transition duration-300 basis-1/3 flex-1 phone:pb-2 md:pb-0 phone:pt-2 md:pt-0">
              <img src={day7} alt="" className="rounded-md mx-auto object-cover shadow-lg" width={'100%'} height={'100%'}/>
            </motion.div>
            <motion.div className="scale-100 hover:scale-105 ease-in transition duration-300 basis-1/3 flex-1 phone:pb-2 md:pb-0 phone:pt-2 md:pt-0">
              <img src={day8} alt="" className="rounded-md mx-auto object-cover shadow-lg" width={'100%'} height={'100%'}/>
            </motion.div>
            <motion.div className="scale-100 hover:scale-105 ease-in transition duration-300 basis-1/3 flex-1 phone:pb-2 md:pb-0 phone:pt-2 md:pt-0">
              <img src={day17} alt="" className="rounded-md mx-auto object-cover shadow-lg" width={'100%'} height={'100%'}/>
            </motion.div>
            <motion.div className="scale-100 hover:scale-105 ease-in transition duration-300 basis-1/3 flex-1 phone:pb-2 md:pb-0 phone:pt-2 md:pt-0">
              <img src={day9} alt="" className="rounded-md mx-auto object-cover shadow-lg" width={'100%'} height={'100%'}/>
            </motion.div>
            <motion.div className="scale-100 hover:scale-105 ease-in transition duration-300 basis-1/3 flex-1 phone:pb-2 md:pb-0 phone:pt-2 md:pt-0">
              <img src={day10} alt="" className="rounded-md mx-auto object-cover shadow-lg" width={'100%'} height={'100%'}/>
            </motion.div>
            <motion.div className="scale-100 hover:scale-105 ease-in transition duration-300 basis-1/3 flex-1 phone:pb-2 md:pb-0 phone:pt-2 md:pt-0">
              <img src={day16} alt="" className="rounded-md mx-auto object-cover shadow-lg" width={'100%'} height={'100%'}/>
            </motion.div>
          </motion.div>
          <motion.div
        className="md:w-2/5 mx-auto text-center"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.5 }}
        transition={{ duration: 0.5 }}
        variants={{
          hidden: { opacity: 0, y: -50 },
          visible: { opacity: 1, y: 0 },
        }}
      >
        <motion.p className="text-jet font-semibold font-playfair text-lg md:text-2xl mt-5 mb-7 hover:text-jet transition duration-500 ease-in-out">What do ya think?</motion.p>
      </motion.div>
          <div className="pt-5">
            <LineGradient />
          </div>
    </section>

  );
};

export default Projects;
