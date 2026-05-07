export function DateSelector({ selectedDate, onDateChange }) {
  const formattedDate = selectedDate.toISOString().split("T")[0]

  return (
    <div style={{
      position: 'absolute',
      top: 20,
      left: 20,
      zIndex: 1000,
      background: 'white',
      padding: '10px',
      borderRadius: '8px',
      boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
      display: 'flex',
      flexDirection: 'column',
      gap: '8px'
    }}>
      <label htmlFor="dateSelect" style={{ fontSize: '14px', fontWeight: 'bold', color: '#333' }}>
        Data do Ortomosaico
      </label>
      <input
        type="date"
        id="dateSelect"
        value={formattedDate}
        onChange={(e) => onDateChange(new Date(e.target.value))}
        style={{
          padding: '8px',
          borderRadius: '4px',
          border: '1px solid #ccc',
          fontSize: '14px',
          cursor: 'pointer',
          fontFamily: 'inherit'
        }}
      />
    </div>
  );
}
