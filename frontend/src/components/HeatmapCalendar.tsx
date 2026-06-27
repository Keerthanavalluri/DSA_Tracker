"use client";

import React, { useMemo } from 'react';
import { format, subDays, startOfWeek, addDays, getDay, differenceInDays } from 'date-fns';

type HeatmapProps = {
  data: Record<string, number>; // "YYYY-MM-DD" -> count
  days: number;
};

export default function HeatmapCalendar({ data, days }: HeatmapProps) {
  const { weeks, maxCount } = useMemo(() => {
    const today = new Date();
    const startDate = subDays(today, days - 1);
    
    // Find the first Sunday before or on startDate
    const calendarStart = startOfWeek(startDate);
    const totalDays = differenceInDays(today, calendarStart) + 1;
    
    const weeksList: { date: Date; count: number; dateStr: string }[][] = [];
    let currentWeek: typeof weeksList[0] = [];
    
    let maxC = 0;

    for (let i = 0; i < totalDays; i++) {
      const d = addDays(calendarStart, i);
      const ds = format(d, 'yyyy-MM-dd');
      const c = data[ds] || 0;
      if (c > maxC) maxC = c;
      
      currentWeek.push({ date: d, count: c, dateStr: ds });
      
      if (currentWeek.length === 7 || i === totalDays - 1) {
        // Pad the last week if it's not full
        while (currentWeek.length < 7) {
          const nextD = addDays(currentWeek[currentWeek.length - 1].date, 1);
          currentWeek.push({ date: nextD, count: 0, dateStr: format(nextD, 'yyyy-MM-dd') });
        }
        weeksList.push(currentWeek);
        currentWeek = [];
      }
    }
    
    return { weeks: weeksList, maxCount: maxC };
  }, [data, days]);

  const getColor = (count: number) => {
    if (count === 0) return 'rgba(255,255,255,0.05)';
    if (maxCount === 0) return 'var(--primary)';
    
    const ratio = count / maxCount;
    // Map from transparent primary to full primary
    return `rgba(99, 102, 241, ${Math.max(0.2, ratio)})`;
  };

  return (
    <div className="glass-card animate-fade-in" style={{ overflowX: 'auto' }}>
      <h3 style={{ marginBottom: '1rem', color: 'var(--foreground)' }}>Submission Heatmap (Last {days} Days)</h3>
      <div style={{ display: 'flex', gap: '4px', paddingBottom: '0.5rem' }}>
        {weeks.map((week, wIndex) => (
          <div key={wIndex} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {week.map((day, dIndex) => (
              <div 
                key={day.dateStr}
                title={`${day.dateStr}: ${day.count} submissions`}
                style={{
                  width: '12px',
                  height: '12px',
                  backgroundColor: getColor(day.count),
                  borderRadius: '2px',
                  transition: 'transform 0.1s',
                  cursor: 'pointer'
                }}
                onMouseEnter={(e) => { e.currentTarget.style.transform = 'scale(1.2)' }}
                onMouseLeave={(e) => { e.currentTarget.style.transform = 'scale(1)' }}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
