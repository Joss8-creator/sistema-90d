#!/usr/bin/env python3
"""
backup.py - Sistema de backup automático para base de datos
Ruta: /home/josuedgg/Documentos/Proyectos/Sistema Base/sistema_90d/backup.py

Gestiona backups automáticos comprimidos de la base de datos SQLite.
Protege contra pérdida de datos por corrupción o eliminación accidental.
"""

from pathlib import Path
from datetime import datetime
import shutil
import gzip
import os


class SistemaBackup:
    """
    Gestiona backups automáticos de la base de datos.
    
    Características:
    - Compresión gzip (reduce tamaño ~70%)
    - Rotación automática (mantiene últimos N backups)
    - Backup incremental (solo si >24h desde último)
    """
    
    def __init__(self, db_path: str, backup_dir: str = 'data/backups'):
        """
        Inicializar sistema de backup.
        
        Args:
            db_path: Ruta a la base de datos SQLite
            backup_dir: Directorio donde guardar backups
        """
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        
        # Crear directorio de backups si no existe
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def crear_backup(self, comprimir: bool = True) -> Path:
        """
        Crear backup de la base de datos con timestamp.
        
        Args:
            comprimir: Si True, comprime con gzip (recomendado)
        
        Returns:
            Path: Ruta del archivo de backup creado
        
        Complejidad: O(n) donde n = tamaño de DB (típicamente <5MB)
        Tiempo: <100ms para DB de 5MB
        """
        if not self.db_path.exists():
            raise FileNotFoundError(f"Base de datos no encontrada: {self.db_path}")
        
        # Generar nombre con timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"sistema_{timestamp}.db"
        
        if comprimir:
            backup_name += '.gz'
        
        backup_path = self.backup_dir / backup_name
        
        # Crear backup
        if comprimir:
            with open(self.db_path, 'rb') as f_in:
                with gzip.open(backup_path, 'wb', compresslevel=6) as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            shutil.copy2(self.db_path, backup_path)
        
        # Calcular tamaño
        tamaño_mb = backup_path.stat().st_size / 1024 / 1024
        
        print(f"✓ Backup creado: {backup_path.name} ({tamaño_mb:.2f} MB)")
        
        return backup_path
    
    def limpiar_backups_antiguos(self, max_backups: int = 30):
        """
        Mantener solo los N backups más recientes.
        Elimina backups antiguos para ahorrar espacio.
        
        Args:
            max_backups: Número máximo de backups a mantener
        """
        # Obtener todos los backups ordenados por fecha (más antiguos primero)
        backups = sorted(self.backup_dir.glob('sistema_*.db*'))
        
        if len(backups) > max_backups:
            # Eliminar los más antiguos
            backups_a_eliminar = backups[:-max_backups]
            
            for backup in backups_a_eliminar:
                backup.unlink()
                print(f"  Eliminado backup antiguo: {backup.name}")
            
            print(f"✓ Limpieza completada: {len(backups_a_eliminar)} backups eliminados")
    
    def backup_automatico_si_necesario(self, intervalo_horas: int = 24):
        """
        Crear backup solo si el último tiene más de N horas.
        Evita backups redundantes.
        
        Args:
            intervalo_horas: Horas mínimas entre backups
        
        Returns:
            bool: True si se creó backup, False si no era necesario
        """
        backups = sorted(self.backup_dir.glob('sistema_*.db*'))
        
        # Si no hay backups, crear uno
        if not backups:
            print("No hay backups previos. Creando primer backup...")
            self.crear_backup()
            return True
        
        # Verificar tiempo desde último backup
        ultimo_backup = backups[-1]
        tiempo_desde_ultimo = datetime.now().timestamp() - ultimo_backup.stat().st_mtime
        horas_desde_ultimo = tiempo_desde_ultimo / 3600
        
        # Si han pasado más de N horas, crear nuevo backup
        if horas_desde_ultimo >= intervalo_horas:
            print(f"Han pasado {horas_desde_ultimo:.1f}h desde último backup. Creando nuevo...")
            self.crear_backup()
            self.limpiar_backups_antiguos()
            return True
        else:
            print(f"Último backup hace {horas_desde_ultimo:.1f}h. No es necesario crear otro.")
            return False
    
    def restaurar_backup(self, backup_path: Path) -> bool:
        """
        Restaurar base de datos desde un backup.
        
        Args:
            backup_path: Ruta del backup a restaurar
        
        Returns:
            bool: True si restauración exitosa
        
        ADVERTENCIA: Esto sobrescribe la base de datos actual.
        """
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup no encontrado: {backup_path}")
        
        # Crear backup de seguridad de la BD actual antes de restaurar
        if self.db_path.exists():
            backup_seguridad = self.db_path.with_suffix('.db.before_restore')
            shutil.copy2(self.db_path, backup_seguridad)
            print(f"✓ Backup de seguridad creado: {backup_seguridad.name}")
        
        # Restaurar
        if backup_path.suffix == '.gz':
            # Descomprimir
            with gzip.open(backup_path, 'rb') as f_in:
                with open(self.db_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            # Copiar directamente
            shutil.copy2(backup_path, self.db_path)
        
        print(f"✓ Base de datos restaurada desde: {backup_path.name}")
        return True
    
    def listar_backups(self) -> list:
        """
        Listar todos los backups disponibles con información.
        
        Returns:
            list: Lista de dicts con info de cada backup
        """
        backups = sorted(self.backup_dir.glob('sistema_*.db*'), reverse=True)
        
        resultado = []
        for backup in backups:
            stat = backup.stat()
            resultado.append({
                'nombre': backup.name,
                'ruta': str(backup),
                'tamaño_mb': stat.st_size / 1024 / 1024,
                'fecha': datetime.fromtimestamp(stat.st_mtime),
                'comprimido': backup.suffix == '.gz'
            })
        
        return resultado
    
    def obtener_estadisticas(self) -> dict:
        """
        Obtener estadísticas del sistema de backup.
        
        Returns:
            dict: Estadísticas (número de backups, espacio usado, etc.)
        """
        backups = list(self.backup_dir.glob('sistema_*.db*'))
        
        if not backups:
            return {
                'num_backups': 0,
                'espacio_total_mb': 0,
                'ultimo_backup': None
            }
        
        espacio_total = sum(b.stat().st_size for b in backups)
        ultimo_backup = max(backups, key=lambda b: b.stat().st_mtime)
        
        return {
            'num_backups': len(backups),
            'espacio_total_mb': espacio_total / 1024 / 1024,
            'ultimo_backup': datetime.fromtimestamp(ultimo_backup.stat().st_mtime),
            'ultimo_backup_nombre': ultimo_backup.name
        }
def ejecutar_backup_automatico():
    """Función de conveniencia para ser llamada desde app.py."""
    from database import DB_PATH
    backup_sistema = SistemaBackup(DB_PATH)
    backup_sistema.backup_automatico_si_necesario()


if __name__ == '__main__':
    """
    Script de prueba y utilidad CLI para gestión de backups.
    """
    import sys
    
    db_path = 'data/sistema.db'
    backup_sistema = SistemaBackup(db_path)
    
    if len(sys.argv) > 1:
        comando = sys.argv[1]
        
        if comando == 'crear':
            backup_sistema.crear_backup()
            print("\n✓ Backup creado exitosamente")
        
        elif comando == 'listar':
            backups = backup_sistema.listar_backups()
            print(f"\n📦 Backups disponibles ({len(backups)}):\n")
            for i, b in enumerate(backups, 1):
                comp = "📦" if b['comprimido'] else "📄"
                print(f"{i}. {comp} {b['nombre']}")
                print(f"   Tamaño: {b['tamaño_mb']:.2f} MB")
                print(f"   Fecha: {b['fecha'].strftime('%Y-%m-%d %H:%M:%S')}")
                print()
        
        elif comando == 'stats':
            stats = backup_sistema.obtener_estadisticas()
            print("\n📊 Estadísticas de Backups:\n")
            print(f"Número de backups: {stats['num_backups']}")
            print(f"Espacio total: {stats['espacio_total_mb']:.2f} MB")
            if stats['ultimo_backup']:
                print(f"Último backup: {stats['ultimo_backup'].strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Archivo: {stats['ultimo_backup_nombre']}")
        
        elif comando == 'limpiar':
            max_backups = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            backup_sistema.limpiar_backups_antiguos(max_backups)
        
        else:
            print(f"Comando desconocido: {comando}")
            print("\nComandos disponibles:")
            print("  python3 backup.py crear    - Crear nuevo backup")
            print("  python3 backup.py listar   - Listar backups disponibles")
            print("  python3 backup.py stats    - Mostrar estadísticas")
            print("  python3 backup.py limpiar [N] - Mantener solo últimos N backups")
    
    else:
        # Modo automático
        print("Sistema de Backup - Modo Automático\n")
        backup_sistema.backup_automatico_si_necesario()
        
        # Mostrar estadísticas
        stats = backup_sistema.obtener_estadisticas()
        print(f"\n📊 Total de backups: {stats['num_backups']}")
        print(f"   Espacio usado: {stats['espacio_total_mb']:.2f} MB")
